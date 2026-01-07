# VerfAi Backend — Team Setup (Minimal)

MGA NEED NYO I INSTALL (AS OF NOW)
Jan 07, 2026

## Prerequisites
- Python 3.10+ installed (Windows recommended)
- A MongoDB Atlas connection string (ask owner)

## Install
1. Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Install backend dependencies:
```powershell
pip install -r backend\requirements.txt
```
Installed packages:
- Django — web framework
- pymongo — MongoDB driver
- python-dotenv — load env vars from `.env`
- dnspython — required for `mongodb+srv` URIs

## Environment
1. Create your env file from the example:
```powershell
Copy-Item backend\.env.example backend\.env
```
2. Edit `backend/.env` and set:
- `DJANGO_SECRET_KEY` — any random string for dev
- `DJANGO_DEBUG=True`
- `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`
- `MONGODB_URI` — your Atlas URI
- `MONGODB_DB_NAME=verfai`

## Run
- Basic checks:
```powershell
python backend\manage.py check
```
- Start server:
```powershell
python backend\manage.py runserver
```
- Health endpoint: http://127.0.0.1:8000/api/health

## Verify MongoDB
- Management command:
```powershell
python backend\manage.py check_mongo
```
Expected output: `{ "ok": true, "ping": { "ok": 1 } }`

## Project Layout (for reference)
- `backend/src/domain` — entities/business rules
- `backend/src/use_cases` — application logic
- `backend/src/infrastructure/mongodb` — DB connection and repos
- `backend/src/interfaces/rest` — web/API adapters
- `backend/src/apps/core` — core Django app (health, commands)

Notes:
- Keep secrets in `backend/.env` (not committed).
- If `mongodb+srv` fails, ensure `dnspython` is installed and your Atlas cluster allows your IP.
