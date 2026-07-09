# `ai_server/` — Reality Lab AI Chatbot

Flask backend that powers the chatbot widget on
[reality.ssu.ac.kr](https://reality.ssu.ac.kr). Answers questions about
the lab (members, publications, research, news) using a hierarchical RAG
over site data + OpenAI Chat Completions.

## Architecture

```
   Browser (chatbot.html)
       │  POST /chat  or  /chat/stream (SSE)
       ▼
   Cloudflare Tunnel (ephemeral cloudflared --url)
       │
       ▼
   ai_chatbot_server.py  (Flask, :4005)
       │
       ├── HierarchicalRetriever  →  hierarchical_rag/<category>/
       │     └── FAISS index + pickled docs, one per category
       │
       └── OpenAI Chat Completions (gpt-5.5 by default)
             └── prompt = system + RAG context + user question
```

The chatbot **has no local model dependency** — it calls the OpenAI API.
No GPU needed. This is a switch from the earlier `llama-server`
(GPT-OSS-120B) setup; the migration commit is on `main` and rollback is
described in `scripts/migrate/README.md`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Returns backend status, model name, RAG-loaded flag, whether an API key is set |
| `POST` | `/heartbeat` | Cheap alive check (used by tunnel monitor) |
| `POST` | `/chat` | Non-streaming Q&A. Body: `{"question": "...", "mode": "deep"\|"search"}` |
| `POST` | `/chat/stream` | SSE streaming version of `/chat` |

`mode="search"` skips the LLM and returns only the retrieved RAG context —
useful for citation-style views.

## Files

| File | Role |
|---|---|
| `ai_chatbot_server.py` | Flask app + OpenAI wrapper (this is the entry point) |
| `hierarchical_retriever.py` | Loads a category-specific FAISS index and formats context |
| `rag_retriever.py` | (legacy) flat retriever, kept for reference |
| `build_knowledge_base.py` | Reads `_data/*.yml` + markdown → `knowledge_base.json` |
| `build_hierarchical_rag.py` | Reads `knowledge_base.json` → per-category FAISS indexes under `hierarchical_rag/` |
| `update_rag.sh` | Runs both builders then restarts the chatbot. Nightly cron. |
| `hierarchical_rag/` | Prebuilt FAISS indexes (committed) so a fresh clone works without rebuilding |
| `knowledge_base.json` | Aggregated documents (committed for the same reason) |
| `name_mapping.json` | English ↔ Korean member-name pairs used during query rewrite |
| `requirements.txt` | Python deps |
| `restart_tunnel.sh` | Kills old `cloudflared --url :4005`, starts new, writes URL to `_data/`, commits + pushes |
| `restart_admin_tunnel.sh` | Same, for the admin CMS on :4010 |
| `monitor_tunnel.sh` | Cron watchdog — restarts the tunnel if the URL stops responding |
| `start_server_and_tunnel.sh` | 08:00 KST — start chatbot + tunnels + admin |
| `stop_ai_server.sh` | 04:00 KST — stop chatbot + tunnels (rest window) |
| `git_push_helper.sh` | `safe_git_push` — rebase-and-retry helper for the tunnel commit scripts |

## Environment

Loaded from `<repo>/.env` if `python-dotenv` is available (bootstrap
installs it). Also honored from the shell:

| Variable | Default | Note |
|---|---|---|
| `OPENAI_API_KEY` | (required) | Set in `.env`. Chatbot logs a warning at startup if missing |
| `OPENAI_MODEL` | `gpt-5.5` | Any model your key can access |
| `OPENAI_BASE_URL` | (OpenAI default) | For OpenAI-compatible gateways |
| `RAG_DIR` | `./hierarchical_rag` | Path to the FAISS indexes |

## Running

```bash
# from the repo root, in the venv the bootstrap script creates
source .venv/bin/activate
python3 ai_server/ai_chatbot_server.py --port 4005
```

Systemd unit for production is in
[`scripts/migrate/systemd/reality-chatbot.service`](../scripts/migrate/systemd/reality-chatbot.service).

## RAG refresh

The RAG index goes stale when `_data/publications.yml`, `_data/members.yml`,
etc. change. The nightly cron rebuilds automatically:

```
0 0 * * * $HOME/Realitylab-site/ai_server/update_rag.sh
```

To refresh on demand without kicking the running chatbot:

```bash
RESTART_CHATBOT=0 ./ai_server/update_rag.sh
```

## Rest window

04:00–08:00 KST the chatbot returns a "💤 쉬는시간" message instead of
calling OpenAI. This was originally for GPU rest; it's kept as a cheap
way to bound API cost. Delete the `is_rest_time()` calls if you want
24/7 service.

## Tunnels

The chatbot's public URL rotates whenever the ephemeral Cloudflare tunnel
restarts. `restart_tunnel.sh` writes the current URL into `_data/` (or
similar committed file) and pushes so the site's chatbot widget picks it
up on the next GitHub Pages build (~1–3 min).

If you want a **stable** URL, switch to a named tunnel:
```bash
cloudflared tunnel login
cloudflared tunnel create reality-chatbot
# then edit ~/.cloudflared/config.yml and add a DNS record
```
`monitor_tunnel.sh` and the crontab still work with a named tunnel; the
auto-commit scripts become unnecessary.
