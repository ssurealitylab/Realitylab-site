/**
 * Reality Lab chatbot, as a Cloudflare Worker.
 *
 * Replaces the Flask server that used to run on a lab PC behind a rotating
 * trycloudflare tunnel: same endpoints (/health, /heartbeat, /chat,
 * /chat/stream) and the same response shapes, so the site only swaps its URL.
 *
 * Lab knowledge is fetched from the published site rather than bundled, so
 * editing members.yml / publications.yml / news.yml and pushing is enough - no
 * redeploy. The corpus is small enough to hand to the model outright, which is
 * why no embedding or vector search is needed here.
 */

const KST_OFFSET_MS = 9 * 60 * 60 * 1000;

const SYSTEM_KO = `당신은 숭실대학교 Reality Lab(리얼리티 연구실)의 AI 어시스턴트입니다.
연구실의 정보, 구성원, 연구 분야, 논문 등에 대한 질문에 친절하고 정확하게 답변해주세요.
제공된 참고자료를 기반으로 답변하되, 참고자료에 없는 내용은 "정확한 정보를 찾지 못했습니다"라고 말씀해주세요.
중요: 참고자료에 나오는 주소, 이름, 고유명사, 숫자는 절대 변경하거나 추측하지 마세요. 그대로 인용하세요.
중요: 답변에 【참고자료】, [출처], (참고자료 1) 같은 인용 마크나 각주를 절대 포함하지 마세요. 자연스러운 문장으로만 답변하세요.
답변은 핵심만 간결하게(2~3문장 이내) 해주세요. 구성원을 물으면 명단을 그대로 간단히 정리해 알려주세요.
답변은 한국어로 해주세요.`;

const SYSTEM_EN = `You are an AI assistant for Reality Lab at Soongsil University.
Answer questions about the lab's information, members, research areas, and publications accurately and helpfully.
Base your answers on the provided reference materials. If information is not available, say so.
IMPORTANT: Never modify or guess addresses, names, proper nouns, or numbers from the reference materials. Quote them exactly as provided.
IMPORTANT: Never include citation marks, footnotes, or references like [1], (source 1) in your answer. Just write naturally.
Keep answers brief and to the point (2-3 sentences). For member questions, simply list the roster.
Answer in English.`;

const CITATION_PATTERNS = [
  /【[^】]*】/g,
  /\[\s*참고자료\s*\d*\s*\]/g,
  /\[\s*출처\s*\d*\s*\]/g,
  /\[\s*reference\s*\d*\s*\]/gi,
  /\[\s*source\s*\d*\s*\]/gi,
  /\(\s*참고자료\s*\d+\s*\)/g,
  /\(\s*source\s*\d+\s*\)/gi,
  /\[\d+\]/g,
];

const stripCitations = (t) =>
  CITATION_PATTERNS.reduce((s, p) => s.replace(p, ''), t || '')
    .replace(/ {2,}/g, ' ')
    .trim();

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors },
  });

const kstNow = () => new Date(Date.now() + KST_OFFSET_MS);
const kstDay = () => kstNow().toISOString().slice(0, 10);

const isRestTime = (env) => {
  if (String(env.REST_WINDOW || '1') !== '1') return false;
  const h = kstNow().getUTCHours();
  return h >= 4 && h < 8;
};

const detectLanguage = (text) => {
  const korean = (text.match(/[가-힣ㄱ-ㅣ]/g) || []).length;
  return korean > text.length * 0.1 ? 'ko' : 'en';
};

/* --------------------------------------------------------------- knowledge */

let kbCache = { at: 0, text: '' };

const clean = (s) => String(s || '').replace(/<br>/g, ', ').trim();

function buildContext(kb) {
  const out = [];
  const m = kb.members || {};
  const st = m.students || {};

  const person = (p) => {
    const name = clean(p.name);
    const ko = clean(p.name_ko);
    const who = ko ? `${ko}(${name})` : name;
    const extra = [clean(p.research), clean(p.university), clean(p.email)].filter(Boolean);
    return `  - ${who}${extra.length ? ' — ' + extra.join(', ') : ''}`;
  };

  out.push('[Reality Lab 현재 구성원]');
  const groups = [
    ['지도교수', m.faculty],
    ['박사과정', st.phd_students],
    ['석사과정', st.ms_students],
    ['인턴', st.interns],
  ];
  for (const [label, list] of groups) {
    if (!list || !list.length) continue;
    out.push(`● ${label}:`);
    list.forEach((p) => out.push(person(p)));
  }

  // Robots last; alumni are deliberately left out of the roster.
  const robots = (m.robots && m.robots.members) || [];
  if (robots.length) {
    out.push('● 연구용 로봇:');
    robots.forEach((r) => {
      const sp = r.specs || {};
      const bits = [
        clean(r.model),
        r.joined ? `합류 ${clean(r.joined)}` : '',
        sp.height ? `키 ${sp.height}` : '',
        sp.dof ? String(sp.dof) : '',
      ].filter(Boolean);
      out.push(`  - ${clean(r.name_ko)}(${clean(r.name)}) — ${bits.join(', ')}`);
    });
  }

  const pubs = kb.publications || [];
  if (pubs.length) {
    out.push('', '[논문]');
    pubs.forEach((p) =>
      out.push(
        `  - ${clean(p.title)} / ${clean(p.authors)} / ${clean(p.venue_short || p.venue)} ${p.year || ''}`
      )
    );
  }

  const news = (kb.news || []).slice(0, 15);
  if (news.length) {
    out.push('', '[최근 소식]');
    news.forEach((n) =>
      out.push(`  - ${clean(n.date)} ${clean(n.title)}: ${clean(n.description).slice(0, 160)}`)
    );
  }

  return out.join('\n');
}

async function getContext(env) {
  const now = Date.now();
  if (kbCache.text && now - kbCache.at < 10 * 60 * 1000) return kbCache.text;
  const res = await fetch(env.KB_URL, { cf: { cacheTtl: 300, cacheEverything: true } });
  if (!res.ok) throw new Error(`kb fetch ${res.status}`);
  const text = buildContext(await res.json());
  kbCache = { at: now, text };
  return text;
}

/* ------------------------------------------------------------- rate limits */

let globalHits = [];

async function checkRateLimit(env, ip) {
  const perDay = parseInt(env.RATE_LIMIT_PER_DAY || '15', 10);
  const perMin = parseInt(env.RATE_LIMIT_GLOBAL_PER_MIN || '60', 10);

  const now = Date.now();
  globalHits = globalHits.filter((t) => now - t < 60000);
  if (globalHits.length >= perMin) return { allowed: false, scope: 'global' };

  if (env.RL) {
    const key = `rl:${kstDay()}:${ip}`;
    const used = parseInt((await env.RL.get(key)) || '0', 10);
    if (used >= perDay) return { allowed: false, scope: 'ip_day' };
    // 30h TTL, so the entry expires on its own once the KST day has rolled over
    await env.RL.put(key, String(used + 1), { expirationTtl: 60 * 60 * 30 });
  }

  globalHits.push(now);
  return { allowed: true, scope: '' };
}

function limitMessage(language, scope, perDay) {
  if (scope === 'global') {
    return language === 'en'
      ? '⚠️ The assistant is a little busy right now. Please try again in a moment!'
      : '⚠️ 지금 이용자가 많아요. 잠시 후 다시 시도해 주세요!';
  }
  return language === 'en'
    ? `🙏 You've used up today's ${perDay} questions! Thanks so much for your curiosity about Reality Lab — please come back and chat with me again tomorrow 😊`
    : `🙏 오늘 준비된 질문 ${perDay}번을 모두 사용하셨어요! Reality Lab에 관심 가져주셔서 정말 감사합니다 — 내일 다시 찾아와 주시면 반갑게 답변해 드릴게요 😊`;
}

/* ------------------------------------------------------------------ openai */

const messagesFor = (question, context, language) => [
  { role: 'system', content: language === 'ko' ? SYSTEM_KO : SYSTEM_EN },
  {
    role: 'user',
    content: context
      ? `${context}\n\n${language === 'ko' ? '질문' : 'Question'}: ${question}`
      : question,
  },
];

// gpt-5.x rejects max_tokens (wants max_completion_tokens) and accepts only the
// default temperature, so neither knob is passed.
const openaiBody = (env, question, context, language, stream) =>
  JSON.stringify({
    model: env.OPENAI_MODEL || 'gpt-5.6-luna',
    messages: messagesFor(question, context, language),
    max_completion_tokens: 1024,
    stream,
  });

const callOpenAI = (env, body) =>
  fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${env.OPENAI_API_KEY}`,
    },
    body,
  });

/* ---------------------------------------------------------------- endpoints */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors });
    }

    if (path === '/health') {
      let kbOk = true;
      try {
        await getContext(env);
      } catch {
        kbOk = false;
      }
      return json({
        status: 'healthy',
        backend: 'openai',
        model_name: env.OPENAI_MODEL || 'gpt-5.6-luna',
        api_key_present: Boolean(env.OPENAI_API_KEY),
        rag_loaded: kbOk,
        rest_time: isRestTime(env),
        hosting: 'cloudflare-worker',
        rate_limit: {
          per_day: parseInt(env.RATE_LIMIT_PER_DAY || '15', 10),
          global_per_min: parseInt(env.RATE_LIMIT_GLOBAL_PER_MIN || '60', 10),
          resets: '00:00 KST',
        },
      });
    }

    if (path === '/heartbeat') {
      return json({ status: 'ok', message: 'Server is alive' });
    }

    if (path === '/chat' || path === '/chat/stream') {
      const streaming = path === '/chat/stream';

      if (isRestTime(env)) {
        const msg = '💤 AI 쉬는시간입니다 (04:00-08:00 KST). 잠시 후 다시 시도해주세요!';
        return streaming
          ? sse([{ text: msg, done: false }, { done: true }])
          : json({ response: msg, status: 'rest_time' });
      }

      let data;
      try {
        data = await request.json();
      } catch {
        data = null;
      }
      if (!data) return json({ error: 'No JSON data provided' }, 400);

      const question = String(data.question || '').trim();
      if (!question) return json({ error: 'No question provided' }, 400);

      const language = detectLanguage(question);
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';

      const { allowed, scope } = await checkRateLimit(env, ip);
      if (!allowed) {
        const msg = limitMessage(language, scope, parseInt(env.RATE_LIMIT_PER_DAY || '15', 10));
        return streaming
          ? sse([{ text: msg, done: false }, { done: true }])
          : json({ response: msg, status: 'rate_limited' });
      }

      let context = '';
      try {
        context = await getContext(env);
      } catch {
        context = '';
      }

      if (data.mode === 'search') {
        return json({
          response: context,
          status: context ? 'success' : 'no_results',
          mode: 'search',
          verified_by_researchers: Boolean(context),
        });
      }

      const started = Date.now();
      const upstream = await callOpenAI(
        env,
        openaiBody(env, question, context, language, streaming)
      );

      if (!upstream.ok || !upstream.body) {
        const err =
          language === 'ko' ? 'AI 서버에 연결할 수 없습니다.' : 'Cannot connect to AI server.';
        return streaming ? sse([{ error: err }]) : json({ error: err, status: 'error' }, 503);
      }

      if (!streaming) {
        const payload = await upstream.json();
        const text = stripCitations(
          (payload.choices && payload.choices[0] && payload.choices[0].message.content) || ''
        );
        return json({
          response: text,
          status: 'success',
          mode: data.mode || 'deep',
          verified_by_researchers: Boolean(context),
        });
      }

      return streamAnswer(upstream, started, Boolean(context));
    }

    return json({ error: 'Not found' }, 404);
  },
};

/* ---------------------------------------------------------------- streaming */

function sse(events) {
  const body = events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join('');
  return new Response(body, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      ...cors,
    },
  });
}

function streamAnswer(upstream, started, verified) {
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const stream = new ReadableStream({
    async start(controller) {
      const send = (obj) => controller.enqueue(encoder.encode(`data: ${JSON.stringify(obj)}\n\n`));
      const reader = upstream.body.getReader();
      let buffer = '';
      try {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            const t = line.trim();
            if (!t.startsWith('data:')) continue;
            const payload = t.slice(5).trim();
            if (payload === '[DONE]') continue;
            try {
              const chunk = JSON.parse(payload);
              const piece =
                chunk.choices && chunk.choices[0] && chunk.choices[0].delta
                  ? chunk.choices[0].delta.content
                  : null;
              if (piece) send({ text: piece, done: false });
            } catch {
              /* partial frame - keep buffering */
            }
          }
        }
        send({
          done: true,
          response_time: Math.round((Date.now() - started) / 100) / 10,
          verified_by_researchers: verified,
        });
      } catch (e) {
        send({ error: String(e) });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      ...cors,
    },
  });
}
