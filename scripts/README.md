# `scripts/`

Operational tooling that doesn't run in the site's request path.

## Layout

| Path | Purpose | Read this when |
|---|---|---|
| [`migrate/`](migrate/) | Move the whole chatbot + admin infra to a new server; clean `.git` history | Handing the lab site off to a new maintainer, or standing up a fresh box |

## Where else scripts live

Not everything is here — subsystem scripts live next to their code:

| Path | What it runs |
|---|---|
| `../ai_server/*.sh` | Chatbot tunnel start/stop/monitor, RAG rebuild. Called by cron. |
| `../admin_cms/set_admin_password.py` | Admin CMS password bootstrap/reset. |
| `../update_version.sh` | Footer version bump; see `../VERSION_UPDATE.md`. |

If you're adding a new script, put it next to the code it controls
unless it spans multiple subsystems (in which case it belongs here).

## See also

- **[`migrate/README.md`](migrate/README.md)** — full server hand-off playbook (this is what you want most of the time)
- **[`../README.md`](../README.md)** — repo overview
