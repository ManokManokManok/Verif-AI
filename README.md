# Verif-AI — Team Guide

Welcome to Verif-AI. This README gives a quick, practical guide for teammates to set up, run, and contribute.

## Stack
- Backend: Django (Python) + MongoDB Atlas via `pymongo`
- Architecture: Clean Architecture (domain/use_cases/infrastructure/interfaces)

## Directory Layout
- `backend/` — Django project and clean-architecture source
  - `verfai/` — Django settings/urls/asgi/wsgi
  - `src/domain` — entities and business rules (framework-agnostic)
  - `src/use_cases` — application logic (interactors)
  - `src/infrastructure/mongodb` — DB connection + repositories
  - `src/interfaces/rest` — web/API adapters
  - `src/apps/core` — core Django app (health + commands)
  - `scripts/check_mongo.py` — simple connectivity check

## Quick Start (Windows)
For detailed steps, see [backend/SETUP_TEAM.md](backend/SETUP_TEAM.md).

```powershell
# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend deps
pip install -r backend\requirements.txt

# Configure env
Copy-Item backend\.env.example backend\.env
# Edit backend/.env to add your MongoDB Atlas URI and DB name

# Verify
python backend\manage.py check
python backend\manage.py check_mongo
python backend\manage.py runserver
# Health: http://127.0.0.1:8000/api/health
```

## Branch Strategy
- Default branch: `main`
- Feature branches: `feat/<topic>` or `fix/<topic>` (e.g., `feat/auth-signup`)
- Pull Requests: target `main`, require review before merge

## Auth Work (for teammates)
- Create a new app under `backend/src/apps/auth` (or similar)
- Wire routes in `backend/verfai/urls.py`
- Keep business rules in `src/domain` and `src/use_cases`
- Use `src/infrastructure/mongodb` for persistence (no direct DB code in views)

## MongoDB Notes
- Atlas SRV URIs require `dnspython` (already in requirements)
- If connection fails: check IP access list and credentials in `.env`

## Useful Commands
```powershell
# Run test health checks
python backend\manage.py check
python backend\manage.py check_mongo

# Warm up models (downloads heavy weights; optional) WITHOUT STARTING SERVER
python backend\manage.py warm_models

# Start dev server with model warm-up (alias) WILL STILL DOWNLOAD MODELS (IF NOT CACHED) WHILE STARTING SERVER
python backend\manage.py runserver_llm
# Defaults to port 8000; to specify: python backend\manage.py runserver_llm 0.0.0.0:8000

# Start dev server
python backend\manage.py runserver
```

## Contributing
- Keep code modular and framework-agnostic in domain/use_cases
- Avoid committing secrets (`backend/.gitignore` ignores `.env`)
- Small PRs with clear descriptions are preferred

## Next Up
- Stub `src/apps/auth` for signup/login
- Define repository interfaces for common domain aggregates (optional)
 - Decide whether to enable startup warm-up via `LLM_WARMUP_ON_START=True`
