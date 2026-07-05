# CLAUDE.md

This file provides coding guidance for agents working in this repository.

## What This Is

Hermes OS Dashboard is a single-file Streamlit app (`app.py`) backed by local SQLite (`hermes_os.db` through `local_db.py`). It shows local tables for an Obsidian note index, AI token spend, campaign goals, ideas, and datastore entries.

## Commands

```bash
pip install -r requirements.txt
streamlit run app.py

pip install -r requirements-dev.txt && playwright install chromium
python shoot.py

python scripts/backup_sqlite.py
python scripts/sync_obsidian.py --vault PATH
python scripts/run_sync.py
python scripts/install_task.py
```

There is no formal test suite, linter, or build step. Verify changes with `python -m py_compile app.py vps/hermes_api.py`, the Streamlit app, or `python shoot.py` when visual checks are needed.

## Secrets

Read configuration through `st.secrets`. Local config lives in `.streamlit/secrets.toml`, which is gitignored.

- `HERMES_API_URL`, `HERMES_API_KEY`: optional, enable the live Hermes chat panel.

`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are no longer needed by the app after the SQLite migration.

## Scope

- Treat work in this repo as software engineering: code, docs, deployment, data sync, and UI verification.
- Keep edits small and aligned with the existing Streamlit and SQLite wrapper patterns.
- Use official provider configuration for coding tools and AI services unless provider documentation says otherwise.

## Architecture

`local_db.py` provides a small Supabase-like query builder on top of SQLite.

- `supabase` reads and writes local tables such as `obsidian_vault`, `mission_control`, `ideas`, and `datastore`.
- `get_admin_client()` returns the same local client for `ai_spend`.

Navigation is URL-driven: `active = st.query_params.get("nav", "memory")`. Sidebar entries are anchor links, and each view block stops after rendering.

Values rendered through `unsafe_allow_html=True` should be escaped with `html.escape()` first.

The live Hermes panel calls the separate FastAPI shim in `vps/hermes_api.py`. The shim wraps the `hermes chat -q` CLI with `subprocess.run` using an argument list, not `shell=True`, and authenticates with a bearer token.

## Database

The local SQLite file is `hermes_os.db` in the project root. `local_db.py` initializes and seeds it when needed. Refresh JSON backups with:

```bash
python scripts/backup_sqlite.py
```
