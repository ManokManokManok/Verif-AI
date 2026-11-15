# Verif-AI — AI-Powered Scam Detection Platform

> Leveraging machine learning and secure audit trails to protect users from scams

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Core Features](#core-features)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## Overview

**Verif-AI** is a scam detection platform that analyzes potentially fraudulent messages, emails, and screenshots. It provides analysis results, user history, and administrative review tools. Results are estimates, not proof that a message is safe or fraudulent.

### Mission

Help users assess suspicious communications with accessible, AI-powered tools.

---

## Key Features

### AI-Powered Detection
- **Text Analysis**: A gatekeeper screens submissions before multi-head BERT classification and generative explanation
- **Scam Categories**: Classifies scams into 15 supported categories
- **Scores and Guidance**: Displays classification scores and explanatory guidance
- **Image Analysis**: Uses Gemini to analyze uploaded screenshots and other images

### Enterprise-Grade Security
- **BCrypt Password Hashing**: 12-round BCrypt for secure credential storage
- **JWT Authentication**: Industry-standard token-based auth with refresh tokens
- **Multi-Factor Authentication (MFA)**: Email-based 2FA for enhanced security
- **Role-Based Access Control (RBAC)**: User roles and permissions
- **Audit Logging**: Security events are logged to file and MongoDB
- **Rate Limiting**: Intelligent rate limiting per endpoint category
- **Input Validation**: Schema-based validation with XSS protection

### Admin Dashboard
- **User Management**: View, activate/deactivate, and manage user accounts
- **Role Management**: Assign and modify user roles and permissions
- **System Monitoring**: Real-time model health and performance metrics
- **Analytics**: Comprehensive analysis statistics and trends
- **Report Handling**: Review and resolve user-submitted reports

---

## Architecture

### Tech Stack

**Backend**
- **Framework**: Django 5.0+ (Python 3.10+)
- **Database**: MongoDB for application data; SQLite for Django internals
- **Architecture**: Clean Architecture (domain/use_cases/infrastructure/interfaces)
- **AI**: Multi-head BERT via ONNX Runtime or PyTorch, plus Gemini for generative analysis

**Frontend**
- **Framework**: React 18+ with Vite
- **State Management**: Context API + Custom Hooks
- **Styling**: Modern CSS with responsive design
- **API Client**: Fetch-based API modules

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Interfaces Layer                          │
│  (REST APIs, CLI commands, web controllers)                  │
│  • backend/src/interfaces/rest/                              │
│  • backend/src/apps/*/views.py                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    Use Cases Layer                           │
│  (Application business logic, orchestration)                 │
│  • backend/src/use_cases/                                    │
│  • Framework-agnostic interactors                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    Domain Layer                              │
│  (Core business entities, rules, interfaces)                 │
│  • backend/src/domain/                                       │
│  • Pure Python, no framework dependencies                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  (External services, database, email)                        │
│  • backend/src/infrastructure/mongodb/                       │
│  • backend/src/infrastructure/email_service.py              │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **MongoDB Atlas Account** ([Sign up](https://www.mongodb.com/cloud/atlas))
- **Git** ([Download](https://git-scm.com/))

### Installation (Windows)

For detailed setup instructions, see [backend/SETUP_TEAM.md](backend/SETUP_TEAM.md).

```powershell
# 1. Clone the repository
git clone https://github.com/ManokManokManok/Verif-AI.git
cd verif-ai

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
pip install -r backend\requirements.txt

# 4. Configure environment variables
Copy-Item backend\.env.example backend\.env
# Edit backend/.env with your MongoDB URI, secrets, Gemini key, and email settings

# 5. Verify installation
python backend\manage.py check
python backend\manage.py check_mongo

# 6. Start development server
python backend\manage.py runserver
# Server: http://127.0.0.1:8000
# Health check: http://127.0.0.1:8000/api/health/

```

For the frontend, open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the address printed by Vite (normally `http://localhost:5173`). The
frontend defaults to the local backend. For a different backend, set
`VITE_API_BASE_URL` to its API URL (including `/api`) and `VITE_API_URL` to
its origin (without `/api`); these settings are used by different API modules.
Ensure the backend CORS configuration and frontend content security policy
permit the selected origin.

### BERT model setup

The backend looks for an ONNX model and `tokenizer.json` in
`backend/models/onnx/`. The tokenizer is included in the repository, but the
large `.onnx` file is Git-ignored, so include it in a submitted project folder
or supply it separately to a fresh clone. Alternatively, if the ONNX assets
are unavailable, the loader attempts
to download the configured PyTorch model from Hugging Face; this requires the
model to be accessible and the required dependencies to be installed. If the
model cannot be loaded, text classification returns `MODEL_NOT_LOADED` (503).

### Environment Configuration

Generate secure secrets:

```powershell
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# JWT secret key (64+ characters recommended)
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Example local `.env` configuration:

```env
# Core settings
DJANGO_SECRET_KEY=<your-django-secret>
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGODB_DB_NAME=verfai

# JWT
JWT_SECRET_KEY=<your-jwt-secret>
JWT_ACCESS_TOKEN_LIFETIME=900      # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# Gemini for explanations, image analysis, and other AI features
GEMINI_ENABLED=true
GEMINI_API_KEY=<your-gemini-api-key>
```

Configure an email backend in `backend/.env` for verification, MFA, and
password-reset emails. For local testing, `EMAIL_BACKEND=mock` writes emails to
the console; use a configured email provider when delivery is needed.

For complete environment variable reference, see [backend/docs/ENVIRONMENT_VARIABLES.md](backend/docs/ENVIRONMENT_VARIABLES.md).

---

## Project Structure

```
verif-ai/
├── backend/                  # Django backend application
│   ├── verfai/              # Django project settings
│   ├── src/
│   │   ├── domain/          # Business entities & rules (framework-agnostic)
│   │   ├── use_cases/       # Application logic & interactors
│   │   ├── infrastructure/  # External services (MongoDB, email)
│   │   ├── interfaces/      # REST API adapters
│   │   └── apps/            # Django apps (core, auth, admin, etc.)
│   ├── tests/               # Backend tests
│   ├── docs/                # Detailed documentation
│   ├── models/              # Local model assets
│   └── manage.py            # Django management script
│
└── frontend/                # React frontend application
    ├── src/
    │   ├── components/      # Reusable React components
    │   ├── pages/           # Page-level components
    │   ├── context/         # React Context providers
    │   ├── hooks/           # Custom React hooks
    │   ├── api/             # API client modules
    │   └── utils/           # Utility functions
    └── tests/               # Frontend tests
```

---

## Core Features

### Authentication & Authorization

**Endpoints**:
- `POST /api/auth/register/` - User registration with email verification
- `POST /api/auth/login/` - Traditional email/password login
- `POST /api/auth/mfa/send/` - Send MFA code via email
- `POST /api/auth/mfa/verify/` - Verify MFA code and authenticate
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout and blacklist tokens
- `POST /api/auth/request-reset/` - Request a password reset code
- `POST /api/auth/reset-password/` - Reset password with email and code

**Features**:
- Strong password policies (8+ chars, mixed case, digits, special characters)
- JWT tokens with configurable lifetimes
- Token blacklisting on logout
- Email-based MFA with 6-digit codes (5-minute expiry)
- Rate limiting per endpoint
- Comprehensive audit logging

### Scam Detection

**Endpoint**: `POST /api/detect/`

**Request**:
```json
{
  "message": "Congratulations! You've won $1,000,000! Click here now!"
}
```

**Example classification response** (selected fields):
```json
{
  "is_scam": true,
  "label": "Scam",
  "scam_score": 95.0,
  "legit_score": 5.0,
  "scam_type": "Prize, Raffle & Reward",
  "type_confidence": 90.0,
  "ref_id": "analysis-reference-id",
  "summary": "The message contains a suspicious prize claim.",
  "key_markers": ["Unexpected prize claim"]
}
```

**Capabilities**:
- 15 scam categories
- Scam and legitimate scores on a 0-100 scale
- Explanation and safety guidance
- Default rate limit: 30 requests per minute (`api_write`), configurable by environment

**Workflow**:
1. The gatekeeper screens the submitted text. It may return a limited or rejected
   result with guidance instead of a classification.
2. Messages routed for analysis are classified by BERT.
3. Generative AI produces an explanation and guidance based on the classification.
4. The backend attempts to save the result in MongoDB. Authenticated users can
   review their saved history; `ref_id` is null if saving fails.

Image analysis uses a separate Gemini-powered flow.

### Admin Dashboard

**Endpoints** (require admin role):
- `GET /api/admin/model-health/` - Model health metrics
- `GET /api/admin/analysis-stats/` - Analysis statistics
- `GET /api/admin/user-stats/` - User statistics
- `GET /api/admin/users/` - List all users (paginated)
- `GET /api/admin/users/<id>/` - Get user details
- `PATCH /api/admin/users/<id>/status/` - Update user status
- `PATCH /api/admin/users/<id>/roles/` - Update user roles
- `DELETE /api/admin/users/<id>/delete/` - Delete user account
- `GET /api/admin/reports/` - List user reports
- `PATCH /api/admin/reports/<id>/` - Update a report or record a review

**Capabilities**:
- User lifecycle management
- Role and permission assignment
- System monitoring and metrics
- Report handling and resolution
- Audit trail access

---

## Development

### Useful Commands

```powershell
# Backend, from the repository root
python backend\manage.py check              # Run Django checks
python backend\manage.py check_mongo        # Verify MongoDB connection
python backend\manage.py runserver          # Start dev server
```

```powershell
# Frontend, from the repository root
cd frontend
npm install                                 # Install dependencies
npm run dev                                 # Start dev server (port 5173)
npm run build                               # Production build
npm run preview                             # Preview production build
```

### Branch Strategy

Suggested Git workflow:

- **Feature branches**: `feat/<topic>` (e.g., `feat/auth-signup`)
- **Fix branches**: `fix/<topic>` (e.g., `fix/login-validation`)
- **Pull Requests**: Target the team's agreed base branch and request review

**Steps**:
1. Create a branch for your changes.
2. Test your code before pushing and resolve conflicts.
3. Submit a pull request and address review feedback.

### Development Guidelines

**Backend Development**:
- Keep domain logic framework-agnostic in `src/domain/`
- Use clean architecture patterns (dependency inversion)
- Write unit tests for use cases
- Validate all inputs with schema validators
- Use repository pattern for data access
- Log security events to audit logger

**Frontend Development**:
- Use functional components with hooks
- Implement proper error boundaries
- Handle loading and error states
- Use environment variables for API URLs
- Follow accessibility guidelines (WCAG 2.1)

**Security**:
- Never commit secrets (use `.env` files)
- Validate all user inputs
- Use parameterized queries (no string interpolation)
- Sanitize output to prevent XSS
- Follow principle of least privilege
- Keep dependencies updated

---

## Testing

### Test Coverage

**Backend**: Python tests
- Unit tests: Domain entities, use cases
- Integration tests: Database and API
- Security tests: Auth, authorization, input validation
- Tests for security, detection, reports, analytics, and admin workflows

**Frontend**: Vitest + React Testing Library
- Component tests
- Integration tests

### Running Tests

Backend tests require `pytest`, which is not included in the backend runtime
requirements. Install it in the active development environment if needed.

```powershell
# Backend, from the repository root
cd backend
python -m pytest tests -v
python -m pytest tests\test_detection_pipeline.py -v
```

```powershell
# Frontend, from the repository root
cd frontend
npm run test:run                            # Run tests once
npm test                                    # Run tests (watch disabled by default)
npm test -- --watch                         # Run tests in watch mode
```

---

## Deployment

### Pre-Deployment Checklist

**Security**:
- [ ] `DJANGO_DEBUG=false`
- [ ] Strong secrets generated (64+ characters)
- [ ] Different secrets for Django and JWT
- [ ] `VALIDATE_SECURITY_CONFIG=true`
- [ ] HTTPS/SSL certificate obtained
- [ ] `.env` file in `.gitignore`

**Configuration**:
- [ ] MongoDB Atlas cluster created
- [ ] BERT model assets available and Gemini configured
- [ ] Email service configured (SendGrid/SMTP)
- [ ] CORS origins configured
- [ ] Allowed hosts configured
- [ ] Rate limits reviewed

**Testing**:
- [ ] All tests passing
- [ ] Security tests passing
- [ ] Database connection verified
- [ ] API endpoints tested

### Deployment Platforms

For detailed deployment instructions, see [backend/docs/DEPLOYMENT.md](backend/docs/DEPLOYMENT.md).

### Production Environment Variables

```env
# Production settings
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<64-char-production-secret>
DJANGO_ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
MONGODB_DB_NAME=verfai_production
MONGODB_REQUIRE_TLS=true

# JWT
JWT_SECRET_KEY=<64-char-jwt-secret>
JWT_ACCESS_TOKEN_LIFETIME=900      # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# Generative AI
GEMINI_ENABLED=true
GEMINI_API_KEY=<your-gemini-api-key>

# Email
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.your-api-key
EMAIL_FROM_ADDRESS=noreply@yourdomain.com

# Or use Nodemailer bridge
# EMAIL_BACKEND=nodemailer
# NODEMAILER_HOST=smtp.gmail.com
# NODEMAILER_PORT=587
# NODEMAILER_SECURE=False
# NODEMAILER_USER=your-smtp-user
# NODEMAILER_PASS=your-smtp-password

# Security
VALIDATE_SECURITY_CONFIG=true

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Documentation

### Complete Documentation

Backend documentation is located in [backend/docs/](backend/docs/).

**For Developers**:
- [API_REFERENCE.md](backend/docs/API_REFERENCE.md) - Common API endpoints
- [SECURITY_BEST_PRACTICES.md](backend/docs/SECURITY_BEST_PRACTICES.md) - Security guidelines
- [SETUP_TEAM.md](backend/SETUP_TEAM.md) - Detailed team setup guide

**For DevOps**:
- [DEPLOYMENT.md](backend/docs/DEPLOYMENT.md) - Production deployment guide
- [ENVIRONMENT_VARIABLES.md](backend/docs/ENVIRONMENT_VARIABLES.md) - Environment config reference

**For Security**:
- [SECURITY.md](backend/docs/SECURITY.md) - Security implementation overview
- [SECURITY_BEST_PRACTICES.md](backend/docs/SECURITY_BEST_PRACTICES.md) - Security standards

### Quick Links

- [API Reference](backend/docs/API_REFERENCE.md) - Selected endpoints with examples
- [Security Guide](backend/docs/SECURITY.md) - Security features and best practices
- [Deployment Guide](backend/docs/DEPLOYMENT.md) - Step-by-step deployment
- [Environment Variables](backend/docs/ENVIRONMENT_VARIABLES.md) - Configuration reference

---

## Contributing

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feat/amazing-feature`
3. **Make your changes** following coding standards
4. **Write/update tests** for your changes
5. **Run tests**: Ensure all tests pass
6. **Commit**: `git commit -m 'feat: add amazing feature'`
7. **Push**: `git push origin feat/amazing-feature`
8. **Open a Pull Request** targeting the agreed base branch

### Code Standards

- Follow PEP 8 (Python) and existing JavaScript conventions
- Write meaningful commit messages
- Keep PRs focused and small
- Include tests for new features
- Update documentation as needed
- No secrets in code (use environment variables)

### Review Process

1. Run relevant automated tests.
2. Request code review and address feedback.
3. Review security implications and update documentation as appropriate.

---

## MongoDB Notes

- **Atlas SRV URIs**: Require `dnspython` package (included in requirements)
- **TLS**: Automatically enforced for remote/Atlas connections
- **Local Development**: TLS is skipped for localhost unless forced; the example
  environment file sets `MONGODB_REQUIRE_TLS=true`
- **Force TLS**: Set `MONGODB_REQUIRE_TLS=true` in `.env`
- **Connection Errors**: Check IP whitelist and credentials in MongoDB Atlas

---

## Security

### Security Features

- BCrypt password hashing (12 rounds)
- JWT token authentication with refresh tokens
- Multi-factor authentication (email-based)
- Role-based access control (RBAC)
- Comprehensive audit logging (file + MongoDB)
- Rate limiting per endpoint category
- Input validation and XSS protection
- HTTPS/HSTS in production
- CSRF protection

### Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email the maintainer directly
3. Include reproduction steps and impact assessment
4. Allow 48 hours for initial response

See [SECURITY.md](backend/docs/SECURITY.md) for full security documentation.

---

## License

No license file is currently included in this repository.

---

**Built by the Verif-AI Team**
