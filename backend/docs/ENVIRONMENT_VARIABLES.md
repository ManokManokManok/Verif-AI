# Environment Variables Reference — Verif-AI Backend

> Complete guide to all environment variables
> Last updated: February 18, 2026

---

## Table of Contents

- [Quick Start](#quick-start)
- [Core Configuration](#core-configuration)
- [Database Configuration](#database-configuration)
- [JWT Configuration](#jwt-configuration)
- [Email Configuration](#email-configuration)
- [Rate Limiting Configuration](#rate-limiting-configuration)
- [Security Configuration](#security-configuration)
- [Blockchain Configuration](#blockchain-configuration)
- [LLM Model Configuration](#llm-model-configuration)
- [Development vs Production](#development-vs-production)

---

## Quick Start

1. Copy the example file:
```powershell
Copy-Item backend\.env.example backend\.env
```

2. Set required variables (minimum viable configuration):
```env
# Required for basic operation
DJANGO_SECRET_KEY=<generate-secret-key>
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGODB_DB_NAME=verfai1
JWT_SECRET_KEY=<generate-jwt-secret>
```

3. Generate secure keys:
```powershell
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# JWT secret key (recommended 64+ characters)
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Core Configuration

### `DJANGO_SECRET_KEY`
**Required:** Yes  
**Type:** String  
**Default:** None  
**Min Length:** 50 characters (64+ recommended for production)

Django's secret key for cryptographic signing. Used for:
- Session security
- CSRF protection
- Password reset tokens

**Security:** Must be unique and kept secret. Rotate periodically in production.

**Example:**
```env
DJANGO_SECRET_KEY=django-insecure-your-secret-key-here-change-in-production
```

---

### `DJANGO_DEBUG`
**Required:** No  
**Type:** Boolean  
**Default:** `False`  
**Values:** `true`, `false`, `1`, `0`, `yes`, `no`

Enable Django debug mode. **MUST be `False` in production.**

**Effects:**
- When `True`: Detailed error pages, no security headers
- When `False`: Generic error pages, security headers enabled (HSTS, SSL redirect, etc.)

**Example:**
```env
DJANGO_DEBUG=true  # Development only
DJANGO_DEBUG=false # Production
```

---

### `DJANGO_ALLOWED_HOSTS`
**Required:** Yes (production)  
**Type:** Comma-separated list  
**Default:** `localhost,127.0.0.1`

Allowed hosts for the application. Required for production deployment.

**Example:**
```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,verif-ai.com,www.verif-ai.com
```

---

### `CORS_ALLOWED_ORIGINS`
**Required:** No  
**Type:** Comma-separated list  
**Default:** `http://localhost:5173,http://127.0.0.1:5173`

CORS origins allowed to access the API.

**Example:**
```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://verif-ai.com
```

---

## Database Configuration

### `MONGODB_URI`
**Required:** Yes  
**Type:** MongoDB connection string  
**Default:** None

MongoDB connection URI. Supports both local and MongoDB Atlas.

**Formats:**
```env
# MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/

# Local MongoDB (development)
MONGODB_URI=mongodb://localhost:27017/

# Local with authentication
MONGODB_URI=mongodb://<username>:<password>@localhost:27017/
```

**Security:**
- Use MongoDB Atlas environment variables for credentials
- Enable IP whitelist in MongoDB Atlas
- Use strong passwords

---

### `MONGODB_DB_NAME`
**Required:** Yes  
**Type:** String  
**Default:** `verfai`

Database name to use within MongoDB.

**Example:**
```env
MONGODB_DB_NAME=verfai1
MONGODB_DB_NAME=verfai_production  # Production
```

---

### `MONGODB_REQUIRE_TLS`
**Required:** No  
**Type:** Boolean  
**Default:** Auto-detected (enforced for remote connections)

Force TLS/SSL for MongoDB connections.

**Notes:**
- Automatically enabled for `mongodb+srv://` URIs (Atlas)
- Set to `true` to enforce TLS for local connections
- Most local dev environments don't use TLS

**Example:**
```env
MONGODB_REQUIRE_TLS=true   # Force TLS everywhere
MONGODB_REQUIRE_TLS=false  # Allow non-TLS (dev only)
```

---

## JWT Configuration

### `JWT_SECRET_KEY`
**Required:** Yes  
**Type:** String  
**Min Length:** 64 characters (production), 32+ (development)

Secret key for signing JWT tokens.

**Security:**
- Must be cryptographically random
- Different from `DJANGO_SECRET_KEY`
- Rotate periodically in production

**Generate:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Example:**
```env
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-64-characters-for-production
```

---

### `JWT_ACCESS_TOKEN_LIFETIME`
**Required:** No  
**Type:** Integer (seconds)  
**Default:** `900` (15 minutes)  
**Recommended:** 300-1800 (5-30 minutes)

Access token expiration time in seconds.

**Security considerations:**
- Shorter = more secure but more refresh requests
- Longer = fewer refreshes but larger attack window

**Example:**
```env
JWT_ACCESS_TOKEN_LIFETIME=900    # 15 minutes (default)
JWT_ACCESS_TOKEN_LIFETIME=1800   # 30 minutes
```

---

### `JWT_REFRESH_TOKEN_LIFETIME`
**Required:** No  
**Type:** Integer (seconds)  
**Default:** `604800` (7 days)  
**Recommended:** 604800-2592000 (7-30 days)

Refresh token expiration time in seconds.

**Example:**
```env
JWT_REFRESH_TOKEN_LIFETIME=604800   # 7 days (default)
JWT_REFRESH_TOKEN_LIFETIME=2592000  # 30 days
```

---

## Email Configuration

### `EMAIL_BACKEND`
**Required:** No  
**Type:** String  
**Default:** `mock`  
**Values:** `mock`, `sendgrid`, `nodemailer`, `smtp`

Email service provider to use.

**Options:**
- `mock`: Console/log output only (development)
- `sendgrid`: SendGrid email service (recommended for production)
- `nodemailer`: Node.js Nodemailer transport (SMTP via Node bridge)
- `smtp`: Standard SMTP server

**Example:**
```env
EMAIL_BACKEND=mock      # Development
EMAIL_BACKEND=sendgrid  # Production with SendGrid
EMAIL_BACKEND=nodemailer  # Production with Nodemailer transport
EMAIL_BACKEND=smtp      # Production with custom SMTP
```

---

### Nodemailer Configuration

Required when `EMAIL_BACKEND=nodemailer`:

#### `NODE_EXECUTABLE`
**Required:** No  
**Default:** `node`

Node.js executable used to run the Nodemailer bridge script.

```env
NODE_EXECUTABLE=node
```

---

#### `NODEMAILER_SCRIPT_PATH`
**Required:** No  
**Default:** `backend/scripts/nodemailer_sender.js`

Absolute path to Nodemailer bridge script. Leave empty to use the default script in this repository.

```env
NODEMAILER_SCRIPT_PATH=
```

---

#### `NODEMAILER_TIMEOUT_SECONDS`
**Required:** No  
**Default:** `15`

Timeout for Nodemailer send operation.

```env
NODEMAILER_TIMEOUT_SECONDS=15
```

---

#### `NODEMAILER_HOST`, `NODEMAILER_PORT`, `NODEMAILER_SECURE`, `NODEMAILER_USER`, `NODEMAILER_PASS`
**Required:** Usually yes (unless your transport does not require auth)

SMTP transport settings for Nodemailer.

If any are omitted, the service falls back to equivalent SMTP variables:
- `NODEMAILER_HOST` → `EMAIL_HOST`
- `NODEMAILER_PORT` → `EMAIL_PORT`
- `NODEMAILER_USER` → `EMAIL_HOST_USER`
- `NODEMAILER_PASS` → `EMAIL_HOST_PASSWORD`

```env
NODEMAILER_HOST=smtp.gmail.com
NODEMAILER_PORT=587
NODEMAILER_SECURE=False
NODEMAILER_USER=yourapp@gmail.com
NODEMAILER_PASS=your-app-password
```

Before using Nodemailer, install dependencies:

```bash
cd backend
npm install
```

---

### SendGrid Configuration

#### `SENDGRID_API_KEY`
**Required:** Only if `EMAIL_BACKEND=sendgrid`  
**Type:** String  

SendGrid API key for sending emails.

**Get API Key:**
1. Sign up at https://sendgrid.com
2. Go to Settings → API Keys
3. Create new API key with "Mail Send" permission

**Example:**
```env
SENDGRID_API_KEY=SG.abc123xyz789...
```

---

#### `SENDGRID_FROM_EMAIL`
**Required:** Only if `EMAIL_BACKEND=sendgrid`  
**Type:** Email address  

Verified sender email address.

**Setup:**
1. Verify sender in SendGrid dashboard
2. Use verified domain or single sender

**Example:**
```env
SENDGRID_FROM_EMAIL=noreply@verif-ai.com
```

---

### SMTP Configuration

Required when `EMAIL_BACKEND=smtp`:

#### `EMAIL_HOST`
SMTP server hostname

```env
EMAIL_HOST=smtp.gmail.com      # Gmail
EMAIL_HOST=smtp.office365.com  # Office 365
EMAIL_HOST=smtp.custom.com     # Custom
```

---

#### `EMAIL_PORT`
SMTP server port

```env
EMAIL_PORT=587   # TLS (recommended)
EMAIL_PORT=465   # SSL
EMAIL_PORT=25    # Unencrypted (not recommended)
```

---

#### `EMAIL_HOST_USER`
SMTP authentication username (usually email address)

```env
EMAIL_HOST_USER=yourapp@gmail.com
```

---

#### `EMAIL_HOST_PASSWORD`
SMTP authentication password or app password

**Gmail:** Requires App Password if 2FA enabled

```env
EMAIL_HOST_PASSWORD=your-smtp-password-or-app-password
```

---

#### `EMAIL_USE_TLS`
Enable TLS encryption (recommended)

```env
EMAIL_USE_TLS=True   # Port 587
EMAIL_USE_SSL=True   # Port 465
```

---

#### `EMAIL_FROM_ADDRESS`
Default FROM address for emails

```env
EMAIL_FROM_ADDRESS=noreply@verif-ai.com
```

---

## Rate Limiting Configuration

All rate limits follow this pattern:
- `REQUESTS`: Number of allowed requests
- `WINDOW`: Time window in seconds
- `BLOCK`: How long to block after exceeding limit

### Authentication Rate Limits

#### Login Attempts
```env
RATE_LIMIT_AUTH_LOGIN_REQUESTS=5     # Default: 5
RATE_LIMIT_AUTH_LOGIN_WINDOW=300     # 5 minutes
RATE_LIMIT_AUTH_LOGIN_BLOCK=900      # 15 minute block
```

#### Registration
```env
RATE_LIMIT_AUTH_REGISTER_REQUESTS=3  # Default: 3
RATE_LIMIT_AUTH_REGISTER_WINDOW=3600 # 1 hour
RATE_LIMIT_AUTH_REGISTER_BLOCK=3600  # 1 hour block
```

#### Password Reset
```env
RATE_LIMIT_PASSWORD_RESET_REQUESTS=3  # Default: 3
RATE_LIMIT_PASSWORD_RESET_WINDOW=3600 # 1 hour
RATE_LIMIT_PASSWORD_RESET_BLOCK=3600  # 1 hour block
```

#### Email Verification
```env
RATE_LIMIT_EMAIL_VERIFICATION_REQUESTS=5  # Default: 5
RATE_LIMIT_EMAIL_VERIFICATION_WINDOW=3600 # 1 hour
RATE_LIMIT_EMAIL_VERIFICATION_BLOCK=1800  # 30 min block
```

#### Token Refresh
```env
RATE_LIMIT_TOKEN_REFRESH_REQUESTS=10  # Default: 10
RATE_LIMIT_TOKEN_REFRESH_WINDOW=60    # 1 minute
RATE_LIMIT_TOKEN_REFRESH_BLOCK=300    # 5 min block
```

---

### MFA Rate Limits

#### MFA Code Sending
```env
RATE_LIMIT_MFA_SEND_REQUESTS=3   # Default: 3
RATE_LIMIT_MFA_SEND_WINDOW=300   # 5 minutes
RATE_LIMIT_MFA_SEND_BLOCK=600    # 10 min block
```

#### MFA Code Verification
```env
RATE_LIMIT_MFA_VERIFY_REQUESTS=5  # Default: 5
RATE_LIMIT_MFA_VERIFY_WINDOW=300  # 5 minutes
RATE_LIMIT_MFA_VERIFY_BLOCK=900   # 15 min block
```

---

### API Rate Limits

#### Read Operations
```env
RATE_LIMIT_API_READ_REQUESTS=100  # Default: 100
RATE_LIMIT_API_READ_WINDOW=60     # 1 minute
RATE_LIMIT_API_READ_BLOCK=60      # 1 min block
```

#### Write Operations
```env
RATE_LIMIT_API_WRITE_REQUESTS=30  # Default: 30
RATE_LIMIT_API_WRITE_WINDOW=60    # 1 minute
RATE_LIMIT_API_WRITE_BLOCK=120    # 2 min block
```

---

### Blockchain Rate Limits

#### Blockchain Read
```env
RATE_LIMIT_BLOCKCHAIN_READ_REQUESTS=50  # Default: 50
RATE_LIMIT_BLOCKCHAIN_READ_WINDOW=60    # 1 minute
RATE_LIMIT_BLOCKCHAIN_READ_BLOCK=60     # 1 min block
```

#### Blockchain Write
```env
RATE_LIMIT_BLOCKCHAIN_WRITE_REQUESTS=10  # Default: 10
RATE_LIMIT_BLOCKCHAIN_WRITE_WINDOW=60    # 1 minute
RATE_LIMIT_BLOCKCHAIN_WRITE_BLOCK=300    # 5 min block
```

---

## Security Configuration

### `VALIDATE_SECURITY_CONFIG`
**Required:** No  
**Type:** Boolean  
**Default:** `false`  
**Recommended:** `true` for production

Run security configuration validation on startup.

**Validates:**
- Secret key strength
- Debug mode settings
- CORS configuration
- JWT configuration
- Blockchain settings

**Example:**
```env
VALIDATE_SECURITY_CONFIG=true  # Recommended
```

**Note:** Validation will exit with error if critical security issues found in production mode.

---

## Blockchain Configuration

### `WEB3_PROVIDER_URL`
**Required:** Only if using blockchain features  
**Type:** URL  

Ethereum node provider URL (Infura, Alchemy, etc.)

**Example:**
```env
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
WEB3_PROVIDER_URL=https://eth-mainnet.alchemyapi.io/v2/YOUR_API_KEY
```

---

### `CONTRACT_ADDRESS`
**Required:** Only if using blockchain features  
**Type:** Ethereum address  

Deployed smart contract address for analysis anchoring.

**Example:**
```env
CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
```

---

### `PRIVATE_KEY`
**Required:** Only if using blockchain features  
**Type:** Private key (hex)  

Private key for contract interaction (admin operations).

**Security:**
- Never commit to version control
- Use deployment wallet with minimal funds
- Rotate regularly

**Example:**
```env
PRIVATE_KEY=0xabcdef123456...
```

---

## LLM Model Configuration

### `LLM_WARMUP_ON_START`
**Required:** No  
**Type:** Boolean  
**Default:** `false`

Pre-load ML models on server startup.

**Effects:**
- `true`: Slower startup, faster first request
- `false`: Faster startup, slower first request

**Example:**
```env
LLM_WARMUP_ON_START=true   # Production (recommended)
LLM_WARMUP_ON_START=false  # Development
```

---

## Development vs Production

### Development Configuration (.env)

```env
# Core
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=django-insecure-dev-key-change-me
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=verfai_dev

# JWT
JWT_SECRET_KEY=dev-jwt-secret-change-me-in-production
JWT_ACCESS_TOKEN_LIFETIME=3600  # 1 hour for dev convenience
JWT_REFRESH_TOKEN_LIFETIME=604800

# Email
EMAIL_BACKEND=mock
EMAIL_FROM_ADDRESS=dev@localhost

# Security
VALIDATE_SECURITY_CONFIG=false

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Models
LLM_WARMUP_ON_START=false
```

---

### Production Configuration (.env)

```env
# Core
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<strong-random-key-64-chars>
DJANGO_ALLOWED_HOSTS=verif-ai.com,www.verif-ai.com,api.verif-ai.com

# Database
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
MONGODB_DB_NAME=verfai_production
MONGODB_REQUIRE_TLS=true

# JWT
JWT_SECRET_KEY=<strong-random-jwt-secret-64-chars>
JWT_ACCESS_TOKEN_LIFETIME=900   # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# Email
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.your-api-key
SENDGRID_FROM_EMAIL=noreply@verif-ai.com

# Security
VALIDATE_SECURITY_CONFIG=true

# CORS
CORS_ALLOWED_ORIGINS=https://verif-ai.com,https://www.verif-ai.com

# Models
LLM_WARMUP_ON_START=true

# Rate Limiting (tighten for production)
RATE_LIMIT_AUTH_LOGIN_REQUESTS=3
RATE_LIMIT_AUTH_LOGIN_WINDOW=300
RATE_LIMIT_AUTH_LOGIN_BLOCK=1800
```

---

## Security Checklist

Before production deployment, verify:

- [ ] `DJANGO_DEBUG=false`
- [ ] `DJANGO_SECRET_KEY` is strong (64+ chars) and unique
- [ ] `JWT_SECRET_KEY` is strong (64+ chars) and different from Django secret
- [ ] `MONGODB_URI` uses strong credentials
- [ ] `MONGODB_REQUIRE_TLS=true` for remote connections
- [ ] `VALIDATE_SECURITY_CONFIG=true`
- [ ] `DJANGO_ALLOWED_HOSTS` contains only your domains
- [ ] `CORS_ALLOWED_ORIGINS` contains only your frontend domains
- [ ] Email backend is configured (`sendgrid` or `smtp`, not `mock`)
- [ ] Rate limits are appropriate for your traffic
- [ ] No secrets committed to version control
- [ ] `.env` file is in `.gitignore`

---

## Troubleshooting

### "JWT_SECRET_KEY is not set"
**Solution:** Add `JWT_SECRET_KEY` to `.env` file:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

### "FATAL: Security configuration error"
**Cause:** Security validation failed  
**Solution:**
1. Check error message for specific issue
2. Verify all required secrets are set
3. Ensure secret keys are long enough
4. Set `VALIDATE_SECURITY_CONFIG=false` for dev (not recommended)

---

### "MongoDB connection failed"
**Causes:**
- Incorrect `MONGODB_URI`
- MongoDB Atlas IP not whitelisted
- Network/firewall issues

**Solution:**
1. Verify URI format
2. Add your IP to MongoDB Atlas whitelist
3. Test connection: `python backend/manage.py check_mongo`

---

### "SendGrid authentication failed"
**Causes:**
- Invalid `SENDGRID_API_KEY`
- Unverified sender email

**Solution:**
1. Verify API key in SendGrid dashboard
2. Verify sender email/domain in SendGrid
3. Check API key permissions (needs "Mail Send")

---

### Rate limit errors in development
**Solution:** Adjust rate limits in `.env`:
```env
RATE_LIMIT_AUTH_LOGIN_REQUESTS=100
RATE_LIMIT_API_READ_REQUESTS=1000
```

---

## References

- [Django Settings](https://docs.djangoproject.com/en/4.2/ref/settings/)
- [MongoDB Connection Strings](https://www.mongodb.com/docs/manual/reference/connection-string/)
- [SendGrid API](https://docs.sendgrid.com/api-reference)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)  
For security considerations, see [SECURITY.md](SECURITY.md)
