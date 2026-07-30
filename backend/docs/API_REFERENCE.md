# API Reference — Verif-AI Backend

> Complete API endpoint documentation
> Last updated: February 18, 2026

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
Production: `https://api.verif-ai.com` (configure in deployment)

---

## Authentication Endpoints

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
  "message": "User registered successfully. Please verify your email."
}
```

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
    "token_type": "Bearer"
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
  "message": "MFA code sent to your email",
  "expires_in": 300
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
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "username": "johndoe",
    "roles": ["user"]
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  }
}
```

#### Error Responses
- `400 Bad Request`: Invalid or expired code
- `401 Unauthorized`: Too many failed attempts (max 3)
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
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
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
- Blacklists both access and refresh tokens
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
  "message": "Verification email sent"
}
```

---

#### 6.2 Verify Email

**Endpoint:** `POST /api/auth/verify-email/`  
**Authentication:** Not required  
**Rate Limit:** 10 requests / 1 hour

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
  "message": "Password reset email sent"
}
```

#### Notes
- Always returns success even if email doesn't exist (security)
- Reset token valid for 1 hour

---

#### 7.2 Reset Password

**Endpoint:** `POST /api/auth/reset-password/`  
**Authentication:** Not required  
**Rate Limit:** 5 requests / 1 hour

#### Request Body
```json
{
  "token": "reset_token_abc123",
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

---

## User Management

### 1. Get User Profile

**Endpoint:** `GET /api/users/profile/`  
**Authentication:** Required (Bearer token)  
**Rate Limit:** 100 requests / 1 minute

#### Request Headers
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "username": "johndoe",
  "roles": ["user"],
  "permissions": ["view_profile", "update_profile", "analyze_content", "view_history"],
  "is_active": true,
  "is_verified": true,
  "created_at": "2026-01-01T00:00:00Z",
  "last_login": "2026-02-18T10:00:00Z"
}
```

---

### 2. Check Permission

**Endpoint:** `POST /api/users/check-permission/`  
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
  "user_id": "user_abc123",
  "permission": "manage_users"
}
```

---

## Admin Endpoints

**Note:** All admin endpoints require admin role

### 1. System Health Metrics

**Endpoint:** `GET /api/admin/model-health/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 50 requests / 1 minute

#### Success Response (200 OK)
```json
{
  "model_loaded": true,
  "last_check": "2026-02-18T10:00:00Z",
  "memory_usage": "2.5 GB",
  "inference_count": 1234
}
```

---

### 2. Analysis Statistics

**Endpoint:** `GET /api/admin/analysis-stats/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 50 requests / 1 minute

#### Query Parameters
- `start_date` (optional): ISO 8601 date
- `end_date` (optional): ISO 8601 date

#### Success Response (200 OK)
```json
{
  "total_analyses": 5678,
  "scam_detected": 234,
  "legitimate": 5444,
  "avg_confidence": 0.87,
  "period": {
    "start": "2026-02-01T00:00:00Z",
    "end": "2026-02-18T23:59:59Z"
  }
}
```

---

### 3. User Statistics

**Endpoint:** `GET /api/admin/user-stats/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 50 requests / 1 minute

#### Success Response (200 OK)
```json
{
  "total_users": 1234,
  "active_users": 890,
  "verified_users": 750,
  "admins": 5,
  "new_users_this_month": 45
}
```

---

### 4. List Users

**Endpoint:** `GET /api/admin/users/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 50 requests / 1 minute

#### Query Parameters
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Items per page
- `search` (optional): Search by email or username
- `role` (optional): Filter by role
- `is_active` (optional): Filter by active status

#### Success Response (200 OK)
```json
{
  "users": [
    {
      "id": "user_abc123",
      "email": "user@example.com",
      "username": "johndoe",
      "roles": ["user"],
      "is_active": true,
      "is_verified": true,
      "created_at": "2026-01-01T00:00:00Z",
      "last_login": "2026-02-18T10:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 62,
    "total_count": 1234,
    "limit": 20
  }
}
```

---

### 5. Get User Details

**Endpoint:** `GET /api/admin/users/<user_id>/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 50 requests / 1 minute

#### Success Response (200 OK)
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "username": "johndoe",
  "roles": ["user"],
  "permissions": ["view_profile", "update_profile"],
  "is_active": true,
  "is_verified": true,
  "created_at": "2026-01-01T00:00:00Z",
  "last_login": "2026-02-18T10:00:00Z",
  "verified_at": "2026-01-01T12:30:00Z"
}
```

---

### 6. Update User Status

**Endpoint:** `PUT /api/admin/users/<user_id>/status/`  
**Authentication:** Required (Admin with `manage_users`)  
**Rate Limit:** 30 requests / 1 minute

#### Request Body
```json
{
  "is_active": false,
  "reason": "Terms of service violation"
}
```

#### Success Response (200 OK)
```json
{
  "message": "User status updated successfully",
  "user_id": "user_abc123",
  "is_active": false
}
```

---

### 7. Update User Roles

**Endpoint:** `PUT /api/admin/users/<user_id>/roles/`  
**Authentication:** Required (Admin with `manage_roles`)  
**Rate Limit:** 30 requests / 1 minute

#### Request Body
```json
{
  "roles": ["moderator"],
  "reason": "Promoted to moderator"
}
```

#### Success Response (200 OK)
```json
{
  "message": "User roles updated successfully",
  "user_id": "user_abc123",
  "roles": ["moderator"]
}
```

---

### 8. Delete User

**Endpoint:** `DELETE /api/admin/users/<user_id>/`  
**Authentication:** Required (Admin with `delete_users`)  
**Rate Limit:** 10 requests / 1 minute

#### Success Response (200 OK)
```json
{
  "message": "User deleted successfully",
  "user_id": "user_abc123"
}
```

---

### 9. List User Reports

**Endpoint:** `GET /api/admin/reports/`  
**Authentication:** Required (Admin)  
**Rate Limit:** 50 requests / 1 minute

#### Query Parameters
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `status` (optional): pending, reviewed, resolved, rejected
- `user_id` (optional): Filter by user

#### Success Response (200 OK)
```json
{
  "reports": [
    {
      "id": "report_xyz789",
      "user_id": "user_abc123",
      "user_email": "user@example.com",
      "analysis_id": "analysis_def456",
      "reason": "Incorrect classification",
      "status": "pending",
      "created_at": "2026-02-18T09:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_count": 89,
    "limit": 20
  }
}
```

---

### 10. Update Report Status

**Endpoint:** `PUT /api/admin/reports/<report_id>/status/`  
**Authentication:** Required (Admin with `manage_user_reports`)  
**Rate Limit:** 30 requests / 1 minute

#### Request Body
```json
{
  "status": "resolved",
  "admin_notes": "Reviewed and corrected classification"
}
```

#### Success Response (200 OK)
```json
{
  "message": "Report status updated successfully",
  "report_id": "report_xyz789",
  "status": "resolved"
}
```

---

## Scam Detection

### 1. Detect Scam

**Endpoint:** `POST /api/detect/`  
**Authentication:** Optional (rate limits differ)  
**Rate Limit:** 30 requests / 1 minute (authenticated), 10 requests / 1 minute (anonymous)

#### Request Body
```json
{
  "message": "Congratulations! You've won $1,000,000! Click here to claim your prize now!"
}
```

#### Validation
- **message**: 1-10,000 characters (10KB limit)

#### Success Response (200 OK)
```json
{
  "is_scam": true,
  "confidence": 0.95,
  "analysis_id": "analysis_ghi012",
  "detected_patterns": [
    "urgency_language",
    "suspicious_links",
    "money_request"
  ],
  "timestamp": "2026-02-18T10:00:00Z"
}
```

#### Response Fields
- `is_scam`: Boolean indicating if message is likely a scam
- `confidence`: Float 0.0-1.0 indicating model confidence
- `analysis_id`: Unique ID for this analysis (can be used for reporting)
- `detected_patterns`: Array of pattern identifiers
- `timestamp`: ISO 8601 timestamp of analysis

---

  "contract_address": "0x123abc..."
}
```

---

## System Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health/`  
**Authentication:** Not required  
**Rate Limit:** None

#### Success Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2026-02-18T10:00:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

---

### 2. MongoDB Health

**Endpoint:** `GET /api/health/mongodb/`  
**Authentication:** Not required  
**Rate Limit:** 100 requests / 1 minute

#### Success Response (200 OK)
```json
{
  "status": "connected",
  "latency_ms": 23,
  "database": "verfai1"
}
```

---

## Error Responses

All error responses follow this format:

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
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

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
    "message": "Rate limit exceeded. Please try again later.",
    "details": {
      "retry_after": 60
    }
  }
}
```

### Rate Limit Categories

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
   → Returns new access_token

4. Logout:
   POST /api/auth/logout/
   → Blacklists both tokens
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
- All endpoints accept and return `application/json`
- Token expiry: Access tokens (15 min), Refresh tokens (7 days)
- Maximum request body size: 10MB
- Email verification tokens expire after 24 hours
- Password reset tokens expire after 1 hour
- MFA codes expire after 5 minutes (max 3 attempts)

---

For implementation details and security considerations, see [SECURITY.md](SECURITY.md)
