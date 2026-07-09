# Reality Lab — Soongsil University

Official website source and management infrastructure for the Reality Lab
at Soongsil University (숭실대학교 리얼리티 연구실).

**Live site**: [reality.ssu.ac.kr](https://reality.ssu.ac.kr)
**Hosted by**: GitHub Pages
**Theme base**: Agency Bootstrap → Jekyll

---

## What lives in this repo

The repo bundles four things that used to live on separate machines:

| Piece | Where | What it does |
|---|---|---|
| **Static site** | `_data/`, `_includes/`, `_layouts/`, `_sass/`, `assets/`, `*.md`, `*.html` | Jekyll source. Built by GitHub Pages, served at reality.ssu.ac.kr |
| **AI Chatbot backend** | [`ai_server/`](ai_server/) | Flask + hierarchical RAG + OpenAI Chat Completions |
| **Admin CMS** | [`admin_cms/`](admin_cms/) | Password-protected UI to edit `_data/*.yml` (publications, members, news) with backups, audit log, and git commit |
| **Ops scripts** | [`scripts/migrate/`](scripts/migrate/), `ai_server/*.sh` | Server bootstrap, cron, tunnel management, history cleanup |

Only the static site is public. The chatbot and admin are reached through
Cloudflare Tunnels whose URLs are auto-committed back into the repo so the
site can link to them.

---

## Quick start (local development)

```bash
git clone git@github.com:ssurealitylab/ssurealitylab.github.io.git
cd ssurealitylab.github.io
bundle install
bundle exec jekyll serve --trace
open http://localhost:4000
```

For chatbot + admin work, follow the setup in [`scripts/migrate/README.md`](scripts/migrate/README.md)
— the same script that bootstraps a fresh production server works locally too.

---

## Editing content

Most non-code changes happen in `_data/`:

| File | What it drives |
|---|---|
| `_data/publications.yml` | All publications (see [`_data/README_PUBLICATIONS.md`](_data/README_PUBLICATIONS.md)) |
| `_data/members.yml` | Faculty / students / interns / alumni |
| `_data/news.yml` | News feed on the homepage |
| `_data/research_areas.yml` | Research area cards |
| `_data/version.yml` | Auto-updated footer version (see [`VERSION_UPDATE.md`](VERSION_UPDATE.md)) |

Two ways to edit them:

1. **Admin CMS** — recommended. Open the admin URL, log in, use the form UI. It validates the schema, keeps a timestamped backup, and commits + pushes for you.
2. **Directly in git** — for large or structural changes. Push to `main`; GitHub Pages rebuilds in 1–3 minutes.

> The `international.md` publication list is **hardcoded HTML**, not driven
> from `publications.yml`. When you add a paper, update **both**. See the
> comment block at the top of `international.md` for the pattern.

---

## Repo layout

```
├── _data/                     Site data (edit these to update the site)
│   ├── publications.yml       All papers — schema in README_PUBLICATIONS.md
│   ├── members.yml            Lab roster
│   ├── news.yml               Homepage news
│   └── ...
├── _includes/                 Reusable Jekyll partials (nav, chatbot widget)
├── _layouts/                  Page templates
├── _sass/                     Sass sources
├── _portfolio/                Portfolio grid entries
├── assets/img/                Site images (publications, members, logos)
├── ai_server/                 Chatbot backend — see ai_server/README.md
├── admin_cms/                 Admin CMS — see admin_cms/README.md
├── scripts/migrate/           Server bootstrap + hand-off — see its README
├── index.md, faculty.md, ...  Top-level Jekyll pages
├── international.md           HARDCODED paper list (see caveat above)
└── _config.yml                Jekyll config
```

Directories intentionally **not** committed (see `.gitignore`):
- `_site/`, `vendor/`, `.venv/` — build/runtime output
- `.env`, `admin_cms/admin_config.json` — secrets
- `finetune_env/`, `reality_lab_qwen*/`, `qwen_reality_lab_lora/` — legacy ML experiments (predate the OpenAI-backed chatbot)

---

## Deployment / hand-off to a new server

Everything needed to move the chatbot + admin + tunnels to a fresh box is
in [`scripts/migrate/`](scripts/migrate/). The new person only needs:
1. This repo's URL
2. An OpenAI API key
3. A password of their choice for the admin UI

Then:
```bash
git clone <this repo>
./scripts/migrate/bootstrap_new_server.sh
# fill in .env when it asks
./scripts/migrate/bootstrap_new_server.sh   # idempotent — resumes from where it stopped
```

See `scripts/migrate/README.md` for the full playbook, systemd units, cron
template, and rollback procedure.

---

## Related docs

- **[`scripts/migrate/README.md`](scripts/migrate/README.md)** — server hand-off playbook
- **[`ai_server/README.md`](ai_server/README.md)** — chatbot internals
- **[`admin_cms/README.md`](admin_cms/README.md)** — admin CMS
- **[`_data/README_PUBLICATIONS.md`](_data/README_PUBLICATIONS.md)** — publications YAML schema
- **[`VERSION_UPDATE.md`](VERSION_UPDATE.md)** — footer version-bump mechanism
- **[`WORKFLOW_SETUP.md`](WORKFLOW_SETUP.md)** — one-time GitHub Actions setup

---

## License

Theme base under MIT (see [`LICENSE.txt`](LICENSE.txt)). Site content
(text, images, member info) belongs to Reality Lab and is not covered by
that license.
