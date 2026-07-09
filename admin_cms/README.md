# `admin_cms/` — Reality Lab Admin CMS

Password-protected editing overlay for `_data/*.yml`. Non-programmer lab
members use it to add publications, update the member list, post news,
etc. Every edit is validated, backed up, audited, and committed to git —
GitHub Pages then rebuilds the public site.

## What you can edit

- **Publications** (`_data/publications.yml`) — add / edit / delete
  entries, upload paper images, set author lists, DOI/PDF links
- **Members** (`_data/members.yml`) — faculty, PhD/MS students, interns,
  alumni; move members between sections; upload profile photos
- **News** (`_data/news.yml`) — post site news with images
- **Research areas**, other data files listed in `config.EDITABLE_FILES`

## Architecture

```
   Browser (any Reality Lab member)
       │  https://admin-<hash>.trycloudflare.com
       ▼
   Cloudflare Tunnel (ephemeral)
       │
       ▼
   admin_server.py  (Flask, :4010)
       │
       ├── auth.py               bcrypt password, rate-limit, lockout
       ├── yaml_manager.py       read/write, path-based edits (jsonpath-like)
       ├── schemas.py            per-file schema validation before write
       ├── backup_manager.py     timestamped backups before every write
       ├── audit_log.py          append-only JSONL of who/what/when
       ├── image_manager.py      upload / list / delete assets/img/**
       └── build_pipeline.py     Jekyll build → smoke test → git push
```

The CMS **serves the actual Jekyll site** with an editing overlay
injected — you see the real page, click a field, edit it, save.

## Endpoints (JSON API)

| Method | Path | Purpose |
|---|---|---|
| `GET` / `POST` | `/login` | Login page (also first-time password setup) |
| `GET` | `/logout` | Log out |
| `GET` | `/` | Serve site with overlay |
| `GET` | `/api/whoami` | Current session's editor name |
| `GET` | `/api/data/<file>` | Fetch a `_data/<file>.yml` as JSON |
| `PUT/POST/DELETE` | `/api/deploy/<file>/<path>` | Edit at a jsonpath |
| `GET` / `POST` | `/api/images/<category>[/upload]` | List / upload images |
| `GET` | `/api/backups` | List timestamped backups |
| `POST` | `/api/backups/<id>/restore` | Roll a file back |
| `POST` | `/api/push` | Git commit + push staged edits |
| `POST` | `/api/build` | Local Jekyll build (smoke test) |
| `POST` | `/api/rag/update` | Trigger `ai_server/update_rag.sh` after content changes |
| `GET` | `/api/audit` | Recent audit log |
| `GET` | `/api/unpushed` | Commits not yet pushed to origin |

## Files

| File | Role |
|---|---|
| `admin_server.py` | Flask entry point |
| `config.py` | Paths, session timeout, rate limits, editable file list |
| `auth.py` | Bcrypt password, session, lockout after N failed logins |
| `yaml_manager.py` | Safe read/write of `_data/*.yml` with jsonpath-style edits |
| `schemas.py` | Per-file validation (title required, year is int, etc.) |
| `backup_manager.py` | Snapshot the file into `backups/` before every write |
| `audit_log.py` | Append `{when, who, action, path, old, new}` to `audit_log.jsonl` |
| `image_manager.py` | Uploads to `assets/img/<category>/`, sanitizes filenames |
| `build_pipeline.py` | `jekyll build` → smoke test → `git commit -m ...` → push |
| `set_admin_password.py` | Bootstrap / reset the login password (see below) |
| `templates/`, `static/` | Overlay UI |
| `backups/` | Auto-snapshots (gitignored) |
| `audit_log.jsonl` | Append-only audit log (gitignored) |
| `admin_config.json` | bcrypt password hash + session secret (gitignored) |

## Setup

### First time on a fresh server

The [`bootstrap_new_server.sh`](../scripts/migrate/bootstrap_new_server.sh)
script prompts for a password automatically. Manually:

```bash
python3 admin_cms/set_admin_password.py
# → prompts for password twice, writes admin_config.json with chmod 600
```

To pass the password non-interactively (e.g. Ansible):
```bash
python3 admin_cms/set_admin_password.py 'my-strong-password'
```

The script preserves any existing `secret_key`, so live sessions survive
a password reset.

### Reset a forgotten password

Run the same command. It overwrites `password_hash` but keeps
`secret_key`. Anyone currently logged in stays logged in.

### Nuke the config entirely

```bash
rm admin_cms/admin_config.json
python3 admin_cms/set_admin_password.py
```
This rotates the session secret too, invalidating every active session.

## Safety features

- **Rate limiting**: `LOGIN_RATE_LIMIT` failed attempts (default 5) triggers a `LOGIN_LOCKOUT_MINUTES` timeout (default 15 min). Configured in `config.py`.
- **Backups**: every write to `_data/*.yml` creates a timestamped backup in `admin_cms/backups/`. Restorable via `/api/backups/<id>/restore` or the UI.
- **Audit log**: every mutation is appended to `audit_log.jsonl` with `{when, who, action, path, old, new}`.
- **Schema validation**: `schemas.py` blocks writes that would break the site (missing required fields, wrong types).
- **Editor identity**: every login collects `user_name`. Audit entries + commit messages record it, so you can trace a bad edit back to the person.
- **Preview before push**: `/api/build` runs a local `jekyll build` and reports errors before you commit.

## Running

```bash
# from repo root, in the venv the bootstrap script creates
source .venv/bin/activate
python3 admin_cms/admin_server.py --port 4010
```

Systemd unit for production is in
[`scripts/migrate/systemd/reality-admin.service`](../scripts/migrate/systemd/reality-admin.service).

## What is intentionally NOT in git

| Path | Why |
|---|---|
| `admin_config.json` | Contains password hash and session secret |
| `backups/` | Local snapshots, can be large |
| `audit_log.jsonl` | Grows unbounded, contains editor names |
| `.edit_lock` | Runtime state |

All are listed in the repo `.gitignore`.
