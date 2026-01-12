# VerfAi Backend (Django + MongoDB)

Minimal starter using Django with a clean architecture layout and MongoDB Atlas.

## Prerequisites
- Python 3.10+
- A MongoDB Atlas connection string
- Windows PowerShell

## Quick Start (Windows)
For teammate-focused steps, see the team guide: [backend/SETUP_TEAM.md](backend/SETUP_TEAM.md).
1. Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r backend\requirements.txt
```
3. Copy env example and set your values:
```powershell
Copy-Item backend\.env.example backend\.env
```
Edit `backend/.env` with `DJANGO_SECRET_KEY`, `MONGODB_URI`, and `MONGODB_DB_NAME`.

4. Run initial checks and start the server:
```powershell
python backend\manage.py check
python backend\manage.py runserver
```
Visit http://127.0.0.1:8000/api/health to confirm health.

## Clean Architecture Layout
- `backend/src/domain`: Entities and business rules
- `backend/src/use_cases`: Interactors / application logic
- `backend/src/infrastructure/mongodb`: Repo + DB connection
- `backend/src/interfaces/rest`: Web/API adapters
- `backend/src/apps/core`: Django app (health route, shared entrypoints)

## Notes
- Default Django DB is SQLite for admin/sessions. Domain data can use MongoDB via `pymongo` repos.
- Your teammates can plug auth into `src/apps/` or new apps while keeping domain/use_cases independent.
