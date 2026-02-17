# Security Overview — Verif-AI Backend

> Last updated: February 16, 2026

## Authentication

| Feature | Implementation |
|---------|---------------|
| Password hashing | BCrypt, 12 rounds (`BCryptPasswordHasher`) |
| Password policy | 8+ chars, upper + lower + digit + special (`PasswordValidator`) |
| JWT tokens | HS256, 24 hours  / 7 day refresh (`JWTService`) |
| Token blacklisting | `MockTokenBlacklistService` (in-memory — swap for Mongo/Redis in prod) |
| Rate limiting | Sliding-window per endpoint (`RateLimiter`) |

### Token Lifecycle

```
Register → (email verification) → Login → Access Token (24 hours)
                                        ↘ Refresh Token (7 days)
Access expires → POST /api/auth/refresh/ → New access token
Logout → Tokens blacklisted
```

## Input Validation

- **Schema-based** via `RequestValidator` / `FieldSchema` (see `validators.py`)
- Rejects unexpected fields
- `sanitize_string()` applies `html.escape()` to prevent stored XSS
- Pre-built validators: login, signup, detect_scam, email_only, password_reset

## Database Security (MongoDB)

- All queries use **parameterised** PyMongo dict queries — no string interpolation
- **TLS enforced automatically** for remote connections (Atlas / cloud)
  - Local dev connects without TLS by default
  - Set `MONGODB_REQUIRE_TLS=true` to force TLS everywhere
- Connection validated with a `ping` on startup

## Rate Limiting

| Endpoint category | Limit |
|-------------------|-------|
| `auth_login` | 5 req / 5 min |
| `auth_register` | 3 req / 1 hour |
| `password_reset` | 3 req / 1 hour |
| `api_read` | 100 req / 1 min |
| `api_write` | 30 req / 1 min |
| `token_refresh` | 10 req / 1 min |

## Audit Logging

All security events are recorded by `AuditLogger` (`infrastructure/audit_logger.py`):

- **File** — `logs/security.log` (10 MB rotate, 5 backups)
- **MongoDB** — `audit_logs` collection (TTL: 90 days)

### Events tracked

| Event | When |
|-------|------|
| `auth.login.success` | Successful login |
| `auth.login.failed` | Bad credentials |
| `auth.logout` | Logout |
| `auth.token.refresh` | Token refresh |
| `user.created` | New registration |
| `user.deleted` | Admin deletes account |
| `user.password.reset.*` | Password reset flow |
| `user.email.verified` | Email verification |
| `authz.role.assigned` | Admin changes roles |

## CSRF & CORS

- Django `CsrfViewMiddleware` is enabled
- REST API endpoints use DRF's `@api_view` (exempt from CSRF by design for token-based auth)
- CORS limited to configured origins (`CORS_ALLOWED_ORIGINS`)

## HTTPS / HSTS

When `DEBUG=False`:
| Setting | Value |
|---------|-------|
| `SECURE_HSTS_SECONDS` | 31536000 (1 year) |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | True |
| `SECURE_SSL_REDIRECT` | True |
| `SESSION_COOKIE_SECURE` | True |
| `CSRF_COOKIE_SECURE` | True |

## Reporting Vulnerabilities

If you discover a security issue, **do not** open a public issue. Instead:

1. Email the project maintainer directly
2. Include reproduction steps and impact assessment
3. Allow 48 hours for initial response

## Known Gaps (Planned)

- [x] MFA / 2FA (email-based — Phase 2) ✅ Implemented
- [x] Real email service (SendGrid / SMTP — Phase 2) ✅ Implemented
- [ ] Formal STRIDE threat model
- [ ] OpenAPI / Swagger documentation

## Multi-Factor Authentication (MFA)

Email-based MFA is available for two-step login:

1. **POST** `/api/auth/mfa/send/` — send credentials → receive 6-digit code via email
2. **POST** `/api/auth/mfa/verify/` — submit code → receive JWT tokens

### Configuration

Set `EMAIL_BACKEND` in `.env` (`sendgrid`, `smtp`, or `mock`).
See `.env.example` for all email-related variables.

### Security Properties

- 6-digit codes generated with `secrets.choice()` (cryptographically secure)
- 5-minute code expiry with MongoDB TTL auto-cleanup
- Max 3 verification attempts per code
- Rate limited: 3 sends per 5 min, 5 verifies per 5 min
- Full audit trail (`MFA_CODE_SENT`, `MFA_CODE_VERIFIED`, `MFA_CODE_FAILED`)
