# Verif-AI — AI-Powered Scam Detection Platform

> Leveraging machine learning and secure audit trails to protect users from scams
> Last updated: February 18, 2026

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

**Verif-AI** is an intelligent scam detection platform that combines advanced machine learning models with strong security controls to identify and verify potentially fraudulent messages, emails, and communications. The platform provides real-time analysis with reliable auditability.

### Mission

Protect users from increasingly sophisticated scam attempts by providing accessible, AI-powered detection tools with transparent, verifiable results.

---

## Key Features

### AI-Powered Detection
- **Advanced NLP Models**: Multi-model ensemble for high-accuracy scam detection
- **Pattern Recognition**: Identifies 15+ scam categories (phishing, urgency tactics, money requests, etc.)
- **Confidence Scoring**: Transparent confidence metrics (0.0-1.0) for each analysis
- **Real-time Analysis**: Sub-second response times for message classification

### Enterprise-Grade Security
- **BCrypt Password Hashing**: 12-round BCrypt for secure credential storage
- **JWT Authentication**: Industry-standard token-based auth with refresh tokens
- **Multi-Factor Authentication (MFA)**: Email-based 2FA for enhanced security
- **Role-Based Access Control (RBAC)**: Granular permissions (user, moderator, admin)
- **Comprehensive Audit Logging**: All security events logged to file + MongoDB
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
- **Database**: MongoDB Atlas (NoSQL)
- **Architecture**: Clean Architecture (domain/use_cases/infrastructure/interfaces)
- **ML Models**: Transformers, scikit-learn, PyTorch

**Frontend**
- **Framework**: React 18+ with Vite
- **State Management**: Context API + Custom Hooks
- **Styling**: Modern CSS with responsive design
- **API Client**: Axios with interceptors

**Smart Contracts**
- **Language**: Solidity 0.8+
- **Framework**: Truffle Suite
- **Network**: Ganache (dev), Ethereum-compatible chains (production)

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
│  • backend/src/infrastructure/email/                         │
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
# Edit backend/.env with your MongoDB URI and secrets

# 5. Verify installation
python backend\manage.py check
python backend\manage.py check_mongo

# 6. Start development server
python backend\manage.py runserver
# Server: http://127.0.0.1:8000
# Health check: http://127.0.0.1:8000/api/health

# 7. (Optional) Start with model warm-up
python backend\manage.py runserver_llm
```

### Environment Configuration

Generate secure secrets:

```powershell
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# JWT secret key (64+ characters recommended)
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Minimum required `.env` variables:

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
```

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
│   ├── tests/               # Comprehensive test suite (84+ tests)
│   ├── docs/                # Detailed documentation
│   ├── logs/                # Application and security logs
│   └── manage.py            # Django management script
│
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable React components
│   │   ├── pages/           # Page-level components
│   │   ├── context/         # React Context providers
│   │   ├── hooks/           # Custom React hooks
│   │   ├── api/             # API client modules
│   │   └── utils/           # Utility functions
│   └── tests/               # Frontend tests
│
├── contracts/               # Ethereum smart contracts
│   ├── contracts/           # Solidity source files
│   ├── migrations/          # Truffle deployment scripts
│   ├── test/                # Smart contract tests (19 tests)
│   └── build/               # Compiled contract artifacts
│
├── ias/                     # IAS (Implementation Assessment System)
└── MODEL TEST/              # ML model testing utilities
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
- `POST /api/auth/forgot-password/` - Request password reset
- `POST /api/auth/reset-password/` - Reset password with token

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

**Response**:
```json
{
  "is_scam": true,
  "confidence": 0.95,
  "analysis_id": "analysis_abc123",
  "detected_patterns": [
    "urgency_language",
    "suspicious_links",
    "money_request"
  ],
  "timestamp": "2026-02-18T10:00:00Z"
}
```

**Capabilities**:
- 15+ scam pattern categories
- Real-time analysis (sub-second response)
- Confidence scoring (0.0-1.0)
- Pattern detection and explanation
- Rate limits: 30/min (authenticated), 10/min (anonymous)

**Workflow**:
1. User performs scam analysis
2. Results stored in MongoDB with unique analysis ID
3. User reviews analysis history and reports
4. Canonical payload created (hash + metadata, no PII)
5. Smart contract called to store payload hash
6. Transaction hash stored in MongoDB
7. Verification compares on-chain vs off-chain data

**Privacy**:
- Stored on-chain: Payload hash, classification, confidence, timestamp
- Never on-chain: Message content, emails, phone numbers, PII

### Admin Dashboard

**Endpoints** (require admin role):
- `GET /api/admin/model-health/` - Model health metrics
- `GET /api/admin/analysis-stats/` - Analysis statistics
- `GET /api/admin/user-stats/` - User statistics
- `GET /api/admin/users/` - List all users (paginated)
- `GET /api/admin/users/<id>/` - Get user details
- `PUT /api/admin/users/<id>/status/` - Activate/deactivate user
- `PUT /api/admin/users/<id>/roles/` - Update user roles
- `DELETE /api/admin/users/<id>/` - Delete user account
- `GET /api/admin/reports/` - List user reports
- `PUT /api/admin/reports/<id>/status/` - Update report status

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
# Backend
python backend\manage.py check              # Run Django checks
python backend\manage.py check_mongo        # Verify MongoDB connection
python backend\manage.py warm_models        # Pre-load ML models
python backend\manage.py runserver          # Start dev server
python backend\manage.py runserver_llm      # Start with model warm-up

# Frontend
cd frontend
npm install                                 # Install dependencies
npm run dev                                 # Start dev server (port 5173)
npm run build                               # Production build
npm run preview                             # Preview production build

# Smart Contracts
cd contracts
npm install                                 # Install dependencies
npm run compile                             # Compile contracts
npm run deploy                              # Deploy to Ganache
npm test                                    # Run contract tests

# Testing
cd backend
python -m pytest tests/                     # Run all tests
python -m pytest tests/test_admin_*.py      # Run admin tests
```

### Branch Strategy

**IMPORTANT**: Follow industry-standard Git workflow

- **Default branch**: `main` (protected)
- **Feature branches**: `feat/<topic>` (e.g., `feat/auth-signup`)
- **Fix branches**: `fix/<topic>` (e.g., `fix/login-validation`)
- **Pull Requests**: Target `main`, require review before merge

**Rules**:
1. **NEVER push directly to `main`**
2. Create feature branch for all changes
3. Test your code before pushing
4. Ensure code is "mergeable" (no conflicts)
5. Submit PR and request review
6. Address review feedback promptly

**Key Branches**:
- `main` - Production-ready code
- `LLM` - AI/ML model development
- _(Add team-specific branches here)_

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

**Backend**: 84+ comprehensive tests
- Unit tests: Domain entities, use cases
- Integration tests: Database and API
- Security tests: Auth, authorization, input validation
- Performance tests: Rate limiting, concurrent requests
- E2E tests: Full user workflows

**Frontend**: Jest + React Testing Library
- Component tests
- Integration tests
- E2E tests with Playwright

**Smart Contracts**: 19 Truffle tests
- Unit tests for all contract functions
- Event emission verification
- Access control tests
- Gas optimization tests

### Running Tests

```powershell
# Backend - All tests
cd backend
python -m pytest tests/ -v

# Backend - Specific test categories
python tests/test_admin_api.py              # Admin API tests
python tests/test_admin_security.py         # Admin security tests
python tests/test_integration_verification.py  # Integration tests (14)
python tests/test_api.py                    # API tests (10)

# Frontend tests
cd frontend
npm test                                    # Run all tests
npm run test:coverage                       # With coverage report

# Smart contract tests
cd contracts
npx truffle test                            # All contract tests (19)
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

Supported platforms:
- **Cloud**: AWS, Azure, Google Cloud Platform
- **Containers**: Docker, Kubernetes
- **PaaS**: Heroku, Railway, Render

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

# Email
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.your-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

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

All documentation is located in [backend/docs/](backend/docs/):

**For Developers**:
- [API_REFERENCE.md](backend/docs/API_REFERENCE.md) - Complete API documentation
- [SECURITY_BEST_PRACTICES.md](backend/docs/SECURITY_BEST_PRACTICES.md) - Security guidelines
- [SETUP_TEAM.md](backend/SETUP_TEAM.md) - Detailed team setup guide

**For DevOps**:
- [DEPLOYMENT.md](backend/docs/DEPLOYMENT.md) - Production deployment guide
- [ENVIRONMENT_VARIABLES.md](backend/docs/ENVIRONMENT_VARIABLES.md) - Environment config reference

**For Security**:
- [SECURITY.md](backend/docs/SECURITY.md) - Security implementation overview
- [SECURITY_BEST_PRACTICES.md](backend/docs/SECURITY_BEST_PRACTICES.md) - Security standards

### Quick Links

- [API Reference](backend/docs/API_REFERENCE.md) - All endpoints with examples
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
8. **Open a Pull Request** targeting `main`

### Code Standards

- Follow PEP 8 (Python) and ESLint configs (JavaScript)
- Write meaningful commit messages
- Keep PRs focused and small
- Include tests for new features
- Update documentation as needed
- No secrets in code (use environment variables)

### Review Process

1. Automated tests must pass
2. At least one code review approval required
3. Security review for security-related changes
4. Documentation review for API changes

---

## MongoDB Notes

- **Atlas SRV URIs**: Require `dnspython` package (included in requirements)
- **TLS**: Automatically enforced for remote/Atlas connections
- **Local Development**: TLS skipped for localhost by default
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

[MIT License](LICENSE) - See LICENSE file for details

---

**Built by the Verif-AI Team**
