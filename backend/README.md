# VerfAi Backend (Django + MongoDB)

Minimal starter using Django with a clean architecture layout and MongoDB Atlas.

## Prerequisites
- Python 3.10+
- A MongoDB Atlas connection string
- Windows PowerShell

## Quick Start (Windows)
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
Edit `backend/.env` with `DJANGO_SECRET_KEY`, `MONGODB_URI`, `MONGODB_DB_NAME`, and `JWT_SECRET_KEY`.

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

## Authentication System

### Overview
This backend implements a comprehensive authentication system with JWT-based stateless authentication and role-based access control (RBAC). The implementation follows clean architecture principles with clear separation of concerns.

### Features Implemented

#### Core Authentication 
- **User Registration**: Email/password signup with validation
- **User Login**: JWT-based authentication with access/refresh tokens
- **Password Security**: Bcrypt hashing with strength validation
- **Role-Based Access Control**: User roles and permissions system
- **Profile Management**: Get and update user profiles
- **Email Verification**: Account verification via email tokens
- **Password Reset**: Secure password reset flow via email
- **Token Blacklisting**: Secure logout with token revocation
- **Token Refresh**: Refresh access tokens using refresh tokens
- **Enhanced Security**: Token validation and blacklisting

### API Endpoints

#### Authentication Endpoints
```
POST /api/auth/register           - User registration
POST /api/auth/login              - User login
POST /api/auth/refresh            - Refresh access token
POST /api/auth/logout             - Logout (blacklist tokens)
POST /api/auth/send-verification  - Send email verification
POST /api/auth/verify-email       - Verify email with token
POST /api/auth/request-reset      - Request password reset
POST /api/auth/reset-password     - Reset password with token
```

#### User Management Endpoints
```
GET  /api/users/profile           - Get current user profile
POST /api/users/check-permission  - Check user permissions
```

### Usage Examples

#### User Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### User Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Email Verification
```bash
# Send verification email
curl -X POST http://localhost:8000/api/auth/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Verify email with token
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "verification_token_here"}'
```

#### Password Reset
```bash
# Request password reset
curl -X POST http://localhost:8000/api/auth/request-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Reset password with token
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_here",
    "new_password": "NewSecurePass123!"
  }'
```

#### Token Refresh
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "refresh_token_here"}'
```

#### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer access_token_here" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "refresh_token_here"}'
```

### Environment Variables

#### Required Variables
```env
DJANGO_SECRET_KEY=your-django-secret-key
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=verfai1
JWT_SECRET_KEY=your-super-secret-jwt-key
```

#### Optional Variables
```env
# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=900      # 15 minutes (default)
JWT_REFRESH_TOKEN_LIFETIME=604800   # 7 days (default)

# Email Configuration (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Redis Configuration (for token blacklisting in production)
REDIS_URL=redis://localhost:6379/0
```

### Security Features

#### Password Security
- **Bcrypt Hashing**: Secure password storage with configurable rounds
- **Password Validation**: Enforces strong password requirements
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

#### JWT Security
- **Short-Lived Access Tokens**: 15 minutes default expiry
- **Refresh Token Rotation**: Secure token refresh mechanism
- **Token Blacklisting**: Revoked tokens stored in database
- **Secure Token Storage**: HttpOnly, SameSite cookies recommended

#### Email Verification
- **Account Verification**: Users must verify email addresses
- **Secure Tokens**: Cryptographically secure verification tokens
- **Token Expiration**: 24-hour expiry for verification tokens

#### Password Reset
- **Secure Reset Flow**: Token-based password reset
- **Token Expiration**: 1-hour expiry for reset tokens
- **Single-Use Tokens**: Tokens invalidated after use

### Database Schema

#### Users Collection
```javascript
{
  "_id": "user_id",
  "email": "user@example.com",
  "password_hash": "bcrypt_hash",
  "roles": ["user"],
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z",
  "verified_at": "2024-01-01T12:30:00Z",
  "password_updated_at": "2024-01-01T13:00:00Z"
}
```

#### Roles Collection
```javascript
{
  "_id": "role_id",
  "name": "admin",
  "permissions": ["create_user", "delete_user", "view_analytics"],
  "description": "System administrator"
}
```

#### Verification Tokens Collection
```javascript
{
  "_id": "token_id",
  "user_id": "user_id",
  "token": "verification_token",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-02T00:00:00Z",
  "is_used": false,
  "used_at": null
}
```

#### Password Reset Tokens Collection
```javascript
{
  "_id": "token_id",
  "user_id": "user_id",
  "token": "reset_token",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z",
  "is_used": false,
  "used_at": null
}
```

#### Blacklisted Tokens Collection
```javascript
{
  "_id": "token_id",
  "token": "blacklisted_jwt_token",
  "blacklisted_at": "2024-01-01T12:00:00Z",
  "expires_at": "2024-01-08T12:00:00Z"
}
```

### Error Responses

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

#### Common Error Codes
- `INVALID_CREDENTIALS` - Wrong email/password
- `PERMISSION_DENIED` - Insufficient permissions
- `TOKEN_EXPIRED` - JWT token has expired
- `TOKEN_INVALID` - JWT token is invalid
- `USER_NOT_FOUND` - User does not exist
- `EMAIL_ALREADY_EXISTS` - Email already registered
- `WEAK_PASSWORD` - Password doesn't meet requirements
- `INVALID_TOKEN` - Verification/reset token is invalid
- `VALIDATION_ERROR` - Input validation failed

### Development Notes

#### Email Service
Currently uses a mock email service that prints to console. For production, replace `MockEmailService` with a real email service (SendGrid, SES, etc.).

#### Token Blacklisting
Currently uses an in-memory mock service. For production, configure Redis or use the MongoDB-based blacklisting service.

#### Default Roles
The system creates users with a default "user" role. Additional roles can be created and managed through the role management system.

## Notes
- Default Django DB is SQLite for admin/sessions. Domain data uses MongoDB via `pymongo` repos.
- All authentication logic is framework-agnostic and can be easily adapted to other frameworks or used in a microservices architecture.
