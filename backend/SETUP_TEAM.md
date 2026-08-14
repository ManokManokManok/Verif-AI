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

### Optional: Start server and warm models
This pre-downloads and loads the models before serving requests (heavy):
```powershell
python backend\manage.py runserver_llm 8000
```
Or warm first, then start:
```powershell
python backend\manage.py warm_models
python backend\manage.py runserver
```

Check model status:
```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/models/status | Select-Object -ExpandProperty Content
```

## Verify MongoDB
- Management command:
```powershell
python backend\manage.py check_mongo
```
Expected output: `{ "ok": true, "ping": { "ok": 1 } }`

## Security Notes

### MongoDB TLS
- **Remote/Atlas connections**: TLS is enforced automatically by `connection.py`.
  No extra steps needed — if your `MONGODB_URI` points to a remote host or uses
  `mongodb+srv://`, the driver will add `tls=true` at connect time.
- **Local development**: TLS is skipped for `localhost` / `127.0.0.1` connections.
- To **force** TLS even locally, add to `.env`:
  ```
  MONGODB_REQUIRE_TLS=true
  ```

### Audit Logging
All security-sensitive actions (login, logout, signup, password resets, role
changes) are automatically logged to:
1. **File** — `backend/logs/security.log` (rotates at 10 MB, keeps 5 backups)
2. **MongoDB** — `audit_logs` collection in the app database

Query audit logs in the Mongo shell:
```js
db.audit_logs.find({ event_type: "auth.login.failed" }).sort({ timestamp: -1 }).limit(10)
```

## Project Layout (for reference)
- `backend/src/domain` — entities/business rules
- `backend/src/use_cases` — application logic
- `backend/src/infrastructure/mongodb` — DB connection and repos
- `backend/src/infrastructure/audit_logger.py` — centralised audit logging
- `backend/src/interfaces/rest` — web/API adapters
- `backend/src/apps/core` — core Django app (health, commands)

Notes:
- Keep secrets in `backend/.env` (not committed).
- If `mongodb+srv` fails, ensure `dnspython` is installed and your Atlas cluster allows your IP.
