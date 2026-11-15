# VerfAi Backend — Team Setup (Minimal)

## Prerequisites
- Python 3.10+ installed (Windows recommended)
- A MongoDB Atlas connection string (ask owner)
- A Gemini API key for generative features

Run the commands below from the repository root.

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
- `JWT_SECRET_KEY` — a secure, stable key
- `GEMINI_API_KEY` — your Gemini API key
- `GEMINI_ENABLED=true`
- `EMAIL_BACKEND` — select and configure an email provider, or use `mock` for
  local testing without sending email

Keep the JWT secret stable so existing tokens and password-reset codes remain
verifiable. See [the example environment file](.env.example) for email,
MFA, and other settings. Never commit your `.env` file.

## BERT model

For the local ONNX backend, provide a matching `.onnx` model file and
`tokenizer.json` in `backend\models\onnx`. The large model is Git-ignored and
must be supplied separately for a fresh clone. If those assets are missing,
the backend attempts to load the configured PyTorch model from Hugging Face.
If neither model can load, text classification returns `MODEL_NOT_LOADED`
with HTTP 503.

## Run
- Basic checks:
```powershell
python backend\manage.py check
```
- Start server:
```powershell
python backend\manage.py runserver
```
- Health endpoint: http://127.0.0.1:8000/api/health/

### Optional: Check model loading

This loads the classifier and reports its status:

```powershell
python backend\manage.py warm_models --targets multihead
```

The command runs in its own process; the server loads the model separately when
needed. To check model status in the running server:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/models/status/ | Select-Object -ExpandProperty Content
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
- **Local development**: TLS is skipped for localhost unless forced.
  The example environment file sets `MONGODB_REQUIRE_TLS=true`. For a local
  MongoDB server without TLS, set it to `false` in your local `.env`.
- To **force** TLS even locally, set:
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
