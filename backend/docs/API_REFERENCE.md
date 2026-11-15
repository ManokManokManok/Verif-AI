# API Reference — Verif-AI Backend

> Reference for commonly used backend endpoints

---

## Table of Contents

- [Authentication Endpoints](#authentication-endpoints)
- [User Management](#user-management)
- [Admin Endpoints](#admin-endpoints)
- [Scam Detection](#scam-detection)
- [System Endpoints](#system-endpoints)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)

---

## Base URL

Development: `http://localhost:8000`  
Production: use the configured backend origin for your deployment.

---

## Authentication Endpoints

Response examples show selected fields; actual responses may include additional
fields. Rate limits shown are defaults and may be configured.

### 1. User Registration

**Endpoint:** `POST /api/auth/register/`  
**Authentication:** Not required  
**Rate Limit:** 3 requests / 1 hour

#### Request Body
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

#### Validation Rules
- **email**: Valid email format, 5-254 characters
- **username**: 3-32 characters, alphanumeric with underscores/hyphens
- **password**: 8-128 characters, must contain:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

#### Success Response (201 Created)
```json
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "username": "johndoe",
    "roles": ["user"],
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-02-18T10:00:00Z"
  },
  "message": "User registered successfully",
  "requires_verification": true
}
```

If an unverified account already exists, the endpoint responds with 200 and
requests a fresh verification code.

#### Error Responses
- `400 Bad Request`: Invalid input or validation failure
- `409 Conflict`: Email already exists
- `429 Too Many Requests`: Rate limit exceeded

---

### 2. User Login (Traditional)

**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required  
**Rate Limit:** 5 requests / 5 minutes

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Login successful",
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "username": "johndoe",
    "roles": ["user"],
    "is_active": true,
    "is_verified": true
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

#### Error Responses
- `400 Bad Request`: Missing email or password
- `401 Unauthorized`: Invalid credentials or inactive account
- `429 Too Many Requests`: Rate limit exceeded

---

### 3. Multi-Factor Authentication (MFA)

#### 3.1 Send MFA Code

**Endpoint:** `POST /api/auth/mfa/send/`  
**Authentication:** Not required  
**Rate Limit:** 3 requests / 5 minutes

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Verification code sent to your email",
  "expires_in_seconds": 300
}
```

#### Notes
- Code is valid for 5 minutes
- 6-digit numeric code sent via email
- Validates credentials before sending code

---

#### 3.2 Verify MFA Code

**Endpoint:** `POST /api/auth/mfa/verify/`  
**Authentication:** Not required  
**Rate Limit:** 5 requests / 5 minutes

#### Request Body
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

#### Success Response (200 OK)
```json
{
  "message": "MFA verification successful",
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "username": "johndoe",
    "roles": ["user"]
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

#### Error Responses
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Invalid or expired code
- `429 Too Many Requests`: Rate limit exceeded

---

### 4. Token Refresh

**Endpoint:** `POST /api/auth/refresh/`  
**Authentication:** Not required (refresh token in body)  
**Rate Limit:** 10 requests / 1 minute

#### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Success Response (200 OK)
```json
{
  "message": "Token refreshed successfully",
  "user": { "id": "user_abc123", "email": "user@example.com" },
  "tokens": {
    "access_token": "<access_token>",
    "refresh_token": "<refresh_token>",
    "token_type": "bearer"
  }
}
```

#### Error Responses
- `400 Bad Request`: Missing refresh token
- `401 Unauthorized`: Invalid or blacklisted refresh token

---

### 5. Logout

**Endpoint:** `POST /api/auth/logout/`  
**Authentication:** Required (Bearer token)  
**Rate Limit:** 30 requests / 1 minute

#### Request Headers
```
Authorization: Bearer <access_token>
```

#### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Success Response (200 OK)
```json
{
  "message": "Logout successful"
}
```

#### Notes
- Blacklists the access token and, when supplied, the refresh token
- Tokens remain blacklisted until expiry

---

### 6. Email Verification

#### 6.1 Send Verification Email

**Endpoint:** `POST /api/auth/send-verification/`  
**Authentication:** Not required  
**Rate Limit:** 5 requests / 1 hour

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Verification email sent successfully"
}
```

---

#### 6.2 Verify Email

**Endpoint:** `POST /api/auth/verify-email/`  
**Authentication:** Not required  
**Rate Limit:** 5 requests / 1 hour

#### Request Body
```json
{
  "token": "verification_token_abc123"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Email verified successfully"
}
```

#### Error Responses
- `400 Bad Request`: Invalid or expired token

The current code-based verification flow uses
`POST /api/auth/verify-email/send-code/` and
`POST /api/auth/verify-email/verify-code/`. The send request takes `email`;
the verify request takes `email` and a six-digit `code`.

---

### 7. Password Reset

#### 7.1 Request Password Reset

**Endpoint:** `POST /api/auth/request-reset/`  
**Authentication:** Not required  
**Rate Limit:** 3 requests / 1 hour

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Success Response (200 OK)
```json
{
  "message": "If an account exists for this email, a password reset code has been sent.",
  "retry_after_seconds": 60,
  "send_limit_reached": false
}
```

#### Notes
- Always returns success even if email doesn't exist (security)
- Reset codes expire after 10 minutes; resending has a 60-second cooldown.

---

#### 7.2 Reset Password

**Endpoint:** `POST /api/auth/reset-password/`  
**Authentication:** Not required  
**Rate Limit:** 3 requests / 1 hour

#### Request Body
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewSecurePass123!"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Password reset successfully"
}
```

#### Error Responses
- `400 Bad Request`: Invalid token or weak password

Existing legacy reset links may also submit `token` and `new_password`.

---

## User Management

### 1. Get User Profile

**Endpoint:** `GET /api/auth/profile/`
**Authentication:** Required (Bearer token)  
**Rate Limit:** 100 requests / 1 minute

#### Request Headers
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
```json
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "username": "johndoe",
    "roles": ["user"],
    "is_active": true,
    "is_verified": true,
    "created_at": "2026-01-01T00:00:00Z",
    "last_login": "2026-02-18T10:00:00Z"
  }
}
```

---

### 2. Check Permission

**Endpoint:** `POST /api/auth/check-permission/`
**Authentication:** Required (Bearer token)  
**Rate Limit:** 100 requests / 1 minute

#### Request Body
```json
{
  "permission": "manage_users",
  "resource": "user:user_xyz789"
}
```

#### Success Response (200 OK)
```json
{
  "has_permission": false,
  "permission": "manage_users",
  "resource": "user:user_xyz789"
}
```

---

## Admin Endpoints

**Note:** All admin endpoints require admin role

### 1. System Health Metrics

**Endpoint:** `GET /api/admin/model-health/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 100 requests / 1 minute (default `api_read`)

#### Success Response (200 OK)
The response contains `success: true` and a `data` object with model health metrics.

---

### 2. Analysis Statistics

**Endpoint:** `GET /api/admin/analysis-stats/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 100 requests / 1 minute (default `api_read`)

#### Query Parameters
- `start_date` (optional): ISO 8601 date
- `end_date` (optional): ISO 8601 date
- `period` (optional): `day`, `week`, `month`, `year`, or `all_time`

#### Success Response (200 OK)
The response contains `success: true` and a `data` object with analysis statistics.

---

### 3. User Statistics

**Endpoint:** `GET /api/admin/user-stats/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 100 requests / 1 minute (default `api_read`)

#### Success Response (200 OK)
The response contains `success: true` and a `data` object with user statistics.
The same optional `start_date`, `end_date`, and `period` filters apply.

---

### 4. List Users

**Endpoint:** `GET /api/admin/users/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 100 requests / 1 minute (default `api_read`)

#### Query Parameters
- `page` (default: 1): Page number
- `limit` (default: 50, max: 100): Items per page
- `search` (optional): Search by email or username
- `role` (optional): Filter by role
- `is_active` (optional): Filter by active status
- `is_verified` (optional): Filter by verification status
- `sort_by` and `sort_order` (optional): Sort field and `asc` or `desc`

#### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "users": [],
    "total": 0,
    "page": 1,
    "limit": 50,
    "total_pages": 0
  }
}
```

---

### 5. Get User Details

**Endpoint:** `GET /api/admin/users/<user_id>/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 100 requests / 1 minute (default `api_read`)

#### Success Response (200 OK)
The response contains `success: true` and a `data` object with user details.

---

### 6. Update User Status

**Endpoint:** `PATCH /api/admin/users/<user_id>/status/`
**Authentication:** Required (Admin)
**Rate Limit:** 30 requests / 1 minute

#### Request Body
```json
{
  "status": "suspended"
}
```

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "User user@example.com status has been set to suspended"
}
```

Supported statuses are `active`, `inactive`, and `suspended`. The endpoint
also accepts the legacy `is_active` boolean.

---

### 7. Update User Roles

**Endpoint:** `PATCH /api/admin/users/<user_id>/roles/`
**Authentication:** Required (Admin)
**Rate Limit:** 30 requests / 1 minute

#### Request Body
```json
{
  "roles": ["user"]
}
```

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Roles updated for user@example.com"
}
```

---

### 8. Delete User

**Endpoint:** `DELETE /api/admin/users/<user_id>/delete/`
**Authentication:** Required (Admin)
**Rate Limit:** 30 requests / 1 minute (default `api_write`)

Use the optional query parameter `hard_delete=true` for permanent deletion;
the default is a soft delete.

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "User user@example.com has been archived"
}
```

---

### 9. List User Reports

**Endpoint:** `GET /api/admin/reports/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 100 requests / 1 minute (default `api_read`)

#### Query Parameters
- `page` (default: 1)
- `limit` (default: 50, max: 100)
- `status` (optional): pending, in_progress, resolved, dismissed

#### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "reports": [],
    "total": 0,
    "page": 1,
    "limit": 50,
    "total_pages": 0
  }
}
```

---

### 10. Get Report Details

**Endpoint:** `GET /api/admin/reports/<report_id>/detail/`
**Authentication:** Required (Admin)

Returns report content and reporter details. When linked to an analysis, the admin-only `analysis` object includes the original message, model verdict, likelihood scores, summary, details, indicators, and any prior human-review history.

---

### 11. Update Report and Record Human Review

**Endpoint:** `PATCH /api/admin/reports/<report_id>/`
**Authentication:** Required (Admin)
**Rate Limit:** 30 requests / 1 minute

#### Request Body
```json
{
  "status": "resolved",
  "resolution_notes": "Reviewed and corrected classification",
  "review": {
    "decision": "confirmed_scam",
    "risk_score": 84,
    "scam_type": "Banking Access & Payment",
    "summary": "This message is a high-risk attempt to steal bank account credentials.",
    "details": "The sender is not an authorized bank domain and the link opens a credential collection page.",
    "key_markers": ["Requests a password through an unverified link"],
    "explanation": "The message impersonates the bank and requests credentials."
  }
}
```

Review decisions are `confirmed_scam`, `confirmed_legitimate`, `inconclusive`, and `needs_more_info`. Confirmed decisions require a human-written `summary` (10-2000 characters) and `explanation` (10-2000 characters). A confirmed scam also requires `risk_score` (whole number, 0-100) and `scam_type`, which must be one of the 15 model-supported categories: Banking Access & Payment; Financial and Investment; Health and Wellness; Impersonation and Authority; International or Cross-Border; Job, Business, and Work-from-Home; Legal and Document; Mobile and Digital; Prize, Raffle & Reward; Property & Rental; Psychological, Urgency, & Emotional; Romance, Dating, and Relationship; Shopping and E-Commerce; Tax, Banking, and Loan; Tech and Online Account. The displayed risk band is derived from the score: Very low (0-19), Low (20-39), Medium (40-69), High (70-89), Very high (90-100). Confirmed legitimate results publish a 0% / Very low human risk estimate. `details` is optional (up to 5000 characters), and `key_markers` is an optional list of up to 10 indicators (up to 200 characters each). Inconclusive and needs-more-information decisions are recorded for admins but do not replace the result shown to the user.

Confirmed decisions become the user-visible reviewed result. The original model output is retained, and every review decision is appended to the analysis review history.

Every admin report update appends an `activity_history` entry containing the acting admin's user ID and email (when available), timestamp, resulting status, action type, any response/resolution notes, and any human-review decision. Support responses are retained as individual activity entries rather than only replacing the latest response.

Reporter-facing report submission and report-history responses expose only public report fields. They omit admin assignment, admin identity, activity history, and internal resolution notes. Resolved reports include the generic message `Resolved by a Verif-AI admin.`; dismissed reports state that they were reviewed by a Verif-AI admin. Support replies are exposed separately as `admin_response` only when the activity was explicitly recorded as a support response.

---

## Scam Detection

### 1. Detect Scam

**Endpoint:** `POST /api/detect/`  
**Authentication:** Optional
**Rate Limit:** 30 requests / 1 minute (default `api_write`)

#### Request Body
```json
{
  "message": "Congratulations! You've won $1,000,000! Click here to claim your prize now!"
}
```

#### Validation
- **message**: 1-10,000 characters (10KB limit)

#### Classification Response (200 OK)

Example selected fields (additional explanation and review fields may be present):
```json
{
  "message": "Congratulations! You've won $1,000,000! Click here to claim your prize now!",
  "ref_id": "analysis-reference-id",
  "is_scam": true,
  "label": "Scam",
  "scam_score": 95.0,
  "legit_score": 5.0,
  "scam_type": "Prize, Raffle & Reward",
  "type_confidence": 90.0,
  "summary": "The message contains a suspicious prize claim.",
  "key_markers": ["Unexpected prize claim"]
}
```

- `scam_score`, `legit_score`, and `type_confidence` use a 0-100 scale.
- `ref_id` is null if the result could not be saved.
- The gatekeeper may instead return `result_type: "gatekeeper"` and
  `route: "limited"` or `"rejected"`, together with guidance rather than
  a BERT classification.
- If the BERT model cannot load, the endpoint returns 503 with error code
  `MODEL_NOT_LOADED`.

---

## System Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health/`  
**Authentication:** Not required  
**Rate Limit:** None

#### Success Response (200 OK)
```json
{
  "status": "ok",
  "service": "verfai-api"
}
```

---

## Error Responses

Many endpoints return errors in this format; details and additional fields
vary by endpoint:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `TOKEN_INVALID` | 401 | JWT token is invalid or malformed |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `USER_NOT_FOUND` | 404 | User does not exist |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `EMAIL_ALREADY_EXISTS` | 409 | Email already registered |
| `WEAK_PASSWORD` | 400 | Password doesn't meet requirements |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limiting

### Rate Limit Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1676721600
```

### Rate Limit Exceeded Response (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please slow down and try again later.",
    "retry_after": 60,
    "retry_after_human": "1 minute"
  }
}
```

### Rate Limit Categories

These are defaults and can be overridden by environment configuration.

| Category | Limit | Window | Description |
|----------|-------|--------|-------------|
| `auth_login` | 5 requests | 5 minutes | Login attempts |
| `auth_register` | 3 requests | 1 hour | New registrations |
| `password_reset` | 3 requests | 1 hour | Password reset requests |
| `email_verification` | 5 requests | 1 hour | Email verification |
| `mfa_send` | 3 requests | 5 minutes | MFA code sending |
| `mfa_verify` | 5 requests | 5 minutes | MFA code verification |
| `api_read` | 100 requests | 1 minute | Read operations |
| `api_write` | 30 requests | 1 minute | Write operations |
| `token_refresh` | 10 requests | 1 minute | Token refresh |

---

## Authentication Flow Examples

### Traditional Login Flow

```
1. POST /api/auth/login/
   → Returns access_token + refresh_token

2. Use access_token in Authorization header:
   Authorization: Bearer <access_token>

3. When access_token expires (15 min):
   POST /api/auth/refresh/
   → Returns a `tokens` object with access and refresh tokens

4. Logout:
   POST /api/auth/logout/
   → Blacklists the access token and the refresh token if supplied
```

### MFA Login Flow

```
1. POST /api/auth/mfa/send/
   → Validates credentials
   → Sends 6-digit code to email

2. User receives code via email

3. POST /api/auth/mfa/verify/
   → Verifies code
   → Returns access_token + refresh_token

4. Use tokens as normal
```

---

## Notes

- All timestamps are in UTC and ISO 8601 format
- Most endpoints accept and return `application/json`; image uploads use multipart form data.
- Default token expiry: access tokens (15 min), refresh tokens (7 days); both are configurable.
- Password reset codes expire after 10 minutes.
- MFA codes expire after 5 minutes (max 3 attempts)

---

For implementation details and security considerations, see [SECURITY.md](SECURITY.md)
