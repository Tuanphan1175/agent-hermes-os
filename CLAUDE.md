# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hermes OS Dashboard — a single-file Streamlit app (`app.py`) backed by Supabase. It's a "cockpit" UI over three Supabase tables: an Obsidian note index (`obsidian_vault`), AI token spend (`ai_spend`), and campaign goals (`mission_control`). Live on Streamlit Community Cloud. Most prose (README, docs, code comments) is Vietnamese; keep new comments in Vietnamese to match.

## Commands

```bash
pip install -r requirements.txt                 # runtime deps (streamlit, supabase, pandas, httpx)
streamlit run app.py                            # run dashboard -> http://localhost:8501

pip install -r requirements-dev.txt && playwright install chromium
python shoot.py                                 # Playwright screenshots of the UI (visual verify)

python scripts/backup_supabase.py               # export 3 tables -> backups/*.json (needs env, see below)
python scripts/sync_obsidian.py --vault PATH    # sync local Obsidian vault -> obsidian_vault table (needs env; --dry-run to preview)
```

There is **no test suite, linter, or build step.** Verification is visual: run the app or `shoot.py`.

## Secrets

App reads everything via `st.secrets` — never hardcode keys. Local config lives in `.streamlit/secrets.toml` (gitignored; copy from `.streamlit/secrets.toml.example`). On Streamlit Cloud, set the same keys under Settings → Secrets.

- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — required; public reads.
- `SUPABASE_SERVICE_ROLE_KEY` — optional; without it the AI Spend panels show a warning instead of data.
- `HERMES_API_URL`, `HERMES_API_KEY` — optional; enable the live Hermes chat panel.

`scripts/backup_supabase.py` reads `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` from env (GitHub Actions secrets), not `st.secrets`.

## Architecture

**Two Supabase clients, by design (`app.py`).** This split is the security model — do not collapse it:
- `supabase` (anon key, module level) reads only RLS-public tables: `obsidian_vault`, `mission_control`.
- `get_admin_client()` (service_role, `@st.cache_resource`) reads `ai_spend`, which has **no anon RLS policy** and is intentionally unreadable by anon. Returns `None` when the key is absent/placeholder; every caller must handle `None`.

**Navigation is URL-driven, not session state.** `active = st.query_params.get("nav", "memory")` picks the view. Sidebar entries are hand-rolled `<a href='?nav=...' target='_self'>` anchors (not `st.button`) so they deep-link. Each view block checks `active` and calls `st.stop()` so only one panel renders per run. Adding a view = add a key to `AGENTS` or `SELF_SECTIONS`, render on its `active` value, `st.stop()`.

- `AGENTS` (claude/openclaw/hermes): per-agent spend filtered by `model_name ILIKE %<key>%`.
- `SELF_SECTIONS` (goals/seo/studio/journal/memory/guide): filter the vault by a substring `match` against `file_path`/`file_name`; `memory` (match `None`) is the full-vault home view.

**XSS:** all DB values rendered through `unsafe_allow_html=True` are passed through `html.escape()` first (see `render_vault_card`). Preserve this when adding markup.

**Hermes live chat (`render_hermes_chat`)** POSTs to a separate FastAPI shim, not Supabase. The shim (`vps/hermes_api.py`) runs on a VPS and wraps the `hermes chat -q` CLI via `subprocess` (arg list, no `shell=True`), Bearer-auth'd with constant-time compare, listening on localhost only. `clean_reply()` strips ANSI + the CLI's box-drawing frame to extract the answer. Hermes has no REST API of its own — the shim exists solely to bridge that gap.

## Database

`security/00_full_setup.sql` is the source of truth for schema + seed + RLS — paste-and-run once in the Supabase SQL Editor. It `DROP`s the three tables first, so re-running wipes data. `security/rls_policies.sql` is the RLS-only subset for when tables already exist. The Streamlit code assumes these exact columns; changing the schema means updating both the SQL and the `pd.to_numeric(...)` coercions in `app.py`.

## Deploy & backup

- Deploys to **Streamlit Community Cloud** (auto-builds on push to `main`). Vercel won't work — Streamlit needs a persistent server + websocket. See `docs/deploy-streamlit-cloud.md`.
- `.github/workflows/daily-backup.yml` runs `scripts/backup_supabase.py` daily (00:00 VN) and commits `backups/*.json`. Needs `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` as Actions secrets.
