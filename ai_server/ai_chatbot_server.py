#!/usr/bin/env python3
"""
Reality Lab AI Chatbot Server
Flask-based server with hierarchical RAG + OpenAI Chat Completions.

Env vars (loaded from .env if python-dotenv is available):
  OPENAI_API_KEY    Required. OpenAI API key.
  OPENAI_MODEL      Optional. Default: "gpt-5.5". Override to a real model id
                    if this deployment does not have access to gpt-5.5.
  OPENAI_BASE_URL   Optional. For OpenAI-compatible gateways.
  RAG_DIR           Optional. Overrides the default RAG directory.
"""

import os
import sys
import json
import re
import argparse
import threading
import time
from datetime import datetime

import pytz
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hierarchical_retriever import HierarchicalRetriever

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
except ImportError:
    pass

from openai import OpenAI, APIConnectionError, APIError

app = Flask(__name__)
CORS(app)

rag_retriever = None
request_lock = threading.Lock()
KST = pytz.timezone('Asia/Seoul')

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL") or None
RAG_DIR = os.environ.get(
    "RAG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "hierarchical_rag"),
)

if not os.environ.get("OPENAI_API_KEY"):
    print("[WARN] OPENAI_API_KEY is not set. /chat will fail until it is provided.", file=sys.stderr)

openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "missing"),
    base_url=OPENAI_BASE_URL,
)

# ---------------------------------------------------------------------------
# Abuse protection: per-client rate limiting.
#
# Only /chat and /chat/stream (which spend OpenAI tokens) are limited; /health
# and /heartbeat are polled by the frontend and stay open. The server sits
# behind a Cloudflare quick tunnel, so request.remote_addr is always the tunnel
# (127.0.0.1); the real visitor IP arrives in CF-Connecting-IP. Keying on that
# gives true per-visitor limits instead of one shared bucket.
#
# Limits are sliding-window, in-memory (single Flask process). Env-overridable.
# A rejected request returns HTTP 200 with a friendly message and never calls
# OpenAI — matching the existing is_rest_time() convention so the chat UI shows
# the notice instead of a generic error, while scripted abuse costs no tokens.
from collections import deque

# Per-visitor DAILY quota. Each visitor gets RL_PER_DAY questions per calendar
# day in KST; the counter resets at KST midnight (00:00) because the per-IP key
# is the KST date string — when the date rolls over, the count starts fresh. A
# small global per-minute cap blunts distributed floods without touching normal
# visitors.
RL_PER_DAY = int(os.environ.get("RATE_LIMIT_PER_DAY", "15"))               # per IP / day (KST)
RL_GLOBAL_PER_MIN = int(os.environ.get("RATE_LIMIT_GLOBAL_PER_MIN", "60"))  # all IPs / 60s

_rl_lock = threading.Lock()
_rl_daily = {}            # ip -> [kst_day_str, count] for the current KST day
_rl_global_min = deque()  # timestamps within last 60s (all clients)


def _client_ip():
    """Real visitor IP behind the Cloudflare tunnel."""
    cf = request.headers.get("CF-Connecting-IP")
    if cf:
        return cf.strip()
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _kst_day():
    """KST calendar date string; changes at 00:00 KST, driving the daily reset."""
    return datetime.now(KST).strftime("%Y-%m-%d")


def check_rate_limit():
    """Return (allowed: bool, scope: str). Records the hit when allowed."""
    now = time.time()
    ip = _client_ip()
    today = _kst_day()
    with _rl_lock:
        # global per-minute safety net (distributed flood protection)
        while _rl_global_min and now - _rl_global_min[0] > 60:
            _rl_global_min.popleft()
        if len(_rl_global_min) >= RL_GLOBAL_PER_MIN:
            return False, "global"

        entry = _rl_daily.get(ip)
        if entry is None or entry[0] != today:
            entry = [today, 0]          # new visitor, or a new KST day → reset
            _rl_daily[ip] = entry
        if entry[1] >= RL_PER_DAY:
            return False, "ip_day"

        # allowed — record the hit
        entry[1] += 1
        _rl_global_min.append(now)

        # opportunistic cleanup of yesterday's stale entries
        if len(_rl_daily) > 4096:
            for k in [k for k, v in _rl_daily.items() if v[0] != today]:
                _rl_daily.pop(k, None)
        return True, ""


def _rate_limit_message(language, scope=""):
    if scope == "global":
        # transient site-wide burst, not the visitor's personal daily cap
        if language == "en":
            return "⚠️ The assistant is a little busy right now. Please try again in a moment!"
        return "⚠️ 지금 이용자가 많아요. 잠시 후 다시 시도해 주세요!"
    # personal daily quota exhausted — warm "come back tomorrow" note
    if language == "en":
        return (f"🙏 You've used up today's {RL_PER_DAY} questions! "
                "Thanks so much for your curiosity about Reality Lab — "
                "please come back and chat with me again tomorrow 😊")
    return (f"🙏 오늘 준비된 질문 {RL_PER_DAY}번을 모두 사용하셨어요! "
            "Reality Lab에 관심 가져주셔서 정말 감사합니다 — "
            "내일 다시 찾아와 주시면 반갑게 답변해 드릴게요 😊")

SYSTEM_PROMPT_KO = """당신은 숭실대학교 Reality Lab(리얼리티 연구실)의 AI 어시스턴트입니다.
연구실의 정보, 구성원, 연구 분야, 논문 등에 대한 질문에 친절하고 정확하게 답변해주세요.
제공된 참고자료를 기반으로 답변하되, 참고자료에 없는 내용은 "정확한 정보를 찾지 못했습니다"라고 말씀해주세요.
중요: 참고자료에 나오는 주소, 이름, 고유명사, 숫자는 절대 변경하거나 추측하지 마세요. 그대로 인용하세요.
중요: 답변에 【참고자료】, [출처], (참고자료 1) 같은 인용 마크나 각주를 절대 포함하지 마세요. 자연스러운 문장으로만 답변하세요.
답변은 한국어로 해주세요."""

SYSTEM_PROMPT_EN = """You are an AI assistant for Reality Lab at Soongsil University.
Answer questions about the lab's information, members, research areas, and publications accurately and helpfully.
Base your answers on the provided reference materials. If information is not available, say so.
IMPORTANT: Never modify or guess addresses, names, proper nouns, or numbers from the reference materials. Quote them exactly as provided.
IMPORTANT: Never include citation marks, footnotes, or references like [1], (source 1), 【reference】 in your answer. Just write naturally.
Answer in English."""


_CITATION_PATTERNS = [
    re.compile(r'【[^】]*】'),
    re.compile(r'\[\s*참고자료\s*\d*\s*\]'),
    re.compile(r'\[\s*출처\s*\d*\s*\]'),
    re.compile(r'\[\s*reference\s*\d*\s*\]', re.IGNORECASE),
    re.compile(r'\[\s*source\s*\d*\s*\]', re.IGNORECASE),
    re.compile(r'\(\s*참고자료\s*\d+\s*\)'),
    re.compile(r'\(\s*source\s*\d+\s*\)', re.IGNORECASE),
    re.compile(r'\[\d+\]'),
]


def _strip_citations(text: str) -> str:
    if not text:
        return text
    for pat in _CITATION_PATTERNS:
        text = pat.sub('', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def is_rest_time():
    """Check if current time is during rest hours (04:00-08:00 KST)"""
    now = datetime.now(KST)
    return 4 <= now.hour < 8


def load_rag():
    global rag_retriever
    try:
        print("Loading hierarchical RAG...")
        rag_retriever = HierarchicalRetriever(RAG_DIR)
        rag_retriever.load()
        print("RAG loaded successfully!")
    except Exception as e:
        print(f"Warning: Failed to load RAG: {e}")
        rag_retriever = None


def detect_language(text):
    korean_chars = sum(1 for c in text if '가' <= c <= '힣' or 'ㄱ' <= c <= 'ㅣ')
    return 'ko' if korean_chars > len(text) * 0.1 else 'en'


def get_rag_context(question, language='ko'):
    if rag_retriever is None:
        return "", False

    try:
        results = rag_retriever.search(question, k=5, min_score=0.15)
        if results:
            context = rag_retriever.format_context(results, language=language)
            has_verified = any(
                r.get('metadata', {}).get('type') == 'qa' or r.get('category') == 'qa'
                for r in results
            )
            return context, has_verified
    except Exception as e:
        print(f"RAG search error: {e}")

    return "", False


def _build_messages(question, context, language):
    system_prompt = SYSTEM_PROMPT_KO if language == 'ko' else SYSTEM_PROMPT_EN
    if context:
        user_message = (
            f"{context}\n\n질문: {question}"
            if language == 'ko'
            else f"{context}\n\nQuestion: {question}"
        )
    else:
        user_message = question
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def call_openai(question, context="", language="ko"):
    """Call OpenAI Chat Completions (non-streaming)."""
    try:
        # gpt-5.x rejects max_tokens (wants max_completion_tokens) and accepts
        # only the default temperature, so neither knob is passed.
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=_build_messages(question, context, language),
            max_completion_tokens=1024,
            stream=False,
            timeout=120,
        )
        content = resp.choices[0].message.content or ""
        return _strip_citations(content)
    except APIConnectionError as e:
        print(f"OpenAI connection error: {e}")
        return None
    except APIError as e:
        print(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        print(f"OpenAI unexpected error: {e}")
        return None


def call_openai_stream(question, context="", language="ko"):
    """Call OpenAI Chat Completions with streaming."""
    try:
        stream = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=_build_messages(question, context, language),
            max_completion_tokens=1024,
            stream=True,
            timeout=120,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content
    except Exception as e:
        # Re-raise so chat_stream's outer except emits an SSE `error` event;
        # the browser routes that into chatbot.html's catch branch that shows
        # the "AI 서버에 문제가 있어요" message. Do not yield the exception
        # text — the client would paint the raw traceback onto the page.
        print(f"OpenAI stream error: {e}")
        raise


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "rag_loaded": rag_retriever is not None,
        "backend": "openai",
        "model_name": OPENAI_MODEL,
        "api_key_present": bool(os.environ.get("OPENAI_API_KEY")),
        "rest_time": is_rest_time(),
        "rate_limit": {
            "per_day": RL_PER_DAY,
            "global_per_min": RL_GLOBAL_PER_MIN,
            "resets": "00:00 KST",
        },
    })


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    return jsonify({"status": "ok", "message": "Server is alive"})


@app.route('/chat', methods=['POST'])
def chat():
    if is_rest_time():
        return jsonify({
            "response": "💤 AI 쉬는시간입니다 (04:00-08:00 KST). 잠시 후 다시 시도해주세요!",
            "status": "rest_time",
        })

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    mode = data.get('mode', 'deep')
    language = detect_language(question)

    # Reject floods before spending tokens (outside request_lock so rejected
    # requests return immediately instead of queueing behind the lock).
    allowed, scope = check_rate_limit()
    if not allowed:
        print(f"[RateLimit] blocked {_client_ip()} scope={scope}")
        return jsonify({
            "response": _rate_limit_message(language, scope),
            "status": "rate_limited",
        })

    print(f"\n[Chat] Mode: {mode}, Language: {language}")
    print(f"[Chat] Question: {question}")

    with request_lock:
        context, verified_by_researchers = get_rag_context(question, language)
        if context:
            print(f"[RAG] Found context ({len(context)} chars), verified={verified_by_researchers}")

        if mode == 'search':
            if context:
                return jsonify({
                    "response": context,
                    "status": "success",
                    "mode": "search",
                    "verified_by_researchers": verified_by_researchers,
                })
            msg = "관련 정보를 찾지 못했습니다." if language == 'ko' else "No relevant information found."
            return jsonify({"response": msg, "status": "no_results", "mode": "search"})

        response_text = call_openai(question, context, language)

        if response_text:
            return jsonify({
                "response": response_text,
                "status": "success",
                "mode": mode,
                "verified_by_researchers": verified_by_researchers,
            })
        return jsonify({
            "error": "AI 서버에 연결할 수 없습니다." if language == 'ko' else "Cannot connect to AI server.",
            "status": "error",
        }), 503


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    if is_rest_time():
        def rest_response():
            yield f"data: {json.dumps({'text': '💤 AI 쉬는시간입니다 (04:00-08:00 KST).', 'done': False})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(rest_response(), mimetype='text/event-stream')

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    language = detect_language(question)

    allowed, scope = check_rate_limit()
    if not allowed:
        print(f"[RateLimit] blocked {_client_ip()} scope={scope} (stream)")
        def limited_response():
            yield f"data: {json.dumps({'text': _rate_limit_message(language, scope), 'done': False})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(limited_response(), mimetype='text/event-stream')

    context, verified_by_researchers = get_rag_context(question, language)

    start_time = time.time()

    def generate():
        try:
            for chunk in call_openai_stream(question, context, language):
                yield f"data: {json.dumps({'text': chunk, 'done': False})}\n\n"
            elapsed = round(time.time() - start_time, 1)
            yield f"data: {json.dumps({'done': True, 'response_time': elapsed, 'verified_by_researchers': verified_by_researchers})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


def main():
    parser = argparse.ArgumentParser(description='Reality Lab AI Chatbot Server')
    parser.add_argument('--port', type=int, default=4005, help='Server port')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host')
    args = parser.parse_args()

    load_rag()

    print(f"\nStarting chatbot server on {args.host}:{args.port}")
    print(f"Backend: OpenAI, Model: {OPENAI_MODEL}")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
