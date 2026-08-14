# Deployment Guide — Verif-AI Backend

> Production deployment guide for Verif-AI
> Last updated: February 18, 2026

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Setup](#environment-setup)
- [MongoDB Atlas Setup](#mongodb-atlas-setup)
- [Email Service Setup](#email-service-setup)
- [Application Deployment](#application-deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

---

## Overview

This guide covers deploying Verif-AI backend to production environments. Supported platforms:
- **Cloud platforms**: AWS, Azure, Google Cloud
- **Container platforms**: Docker, Kubernetes
- **Platform-as-a-Service**: Heroku, Railway, Render

Choose the deployment method that best fits your infrastructure.

---

## Prerequisites

### Required Services

- **Python 3.10+** runtime environment
- **MongoDB Atlas** (or self-hosted MongoDB 5.0+)
- **Email service** (SendGrid recommended)
- **SSL/TLS certificate** for HTTPS
- **Domain name** (optional but recommended)

### Required Accounts

- [ ] MongoDB Atlas account
- [ ] SendGrid account (or SMTP provider)
- [ ] Cloud platform account (AWS/Azure/GCP)
- [ ] Domain registrar (if using custom domain)

---

## Pre-Deployment Checklist

### Security

- [ ] All secrets are in environment variables (not in code)
- [ ] `.env` file is in `.gitignore`
- [ ] Strong secret keys generated (64+ characters)
- [ ] Different secrets for JWT and Django
- [ ] `DJANGO_DEBUG=false`
- [ ] `VALIDATE_SECURITY_CONFIG=true`
- [ ] HTTPS/SSL certificate obtained

### Configuration

- [ ] Production environment variables prepared
- [ ] MongoDB Atlas cluster created
- [ ] Email service configured
- [ ] CORS origins configured
- [ ] Allowed hosts configured
- [ ] Rate limits configured

### Testing

- [ ] All tests passing locally
- [ ] Security tests passing
- [ ] Integration tests passing
- [ ] API endpoints tested
- [ ] Database connection tested

---

## Environment Setup

### 1. Generate Production Secrets

```powershell
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# JWT secret key (64+ characters recommended)
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Save these in a secure location (password manager, secrets vault).

---

### 2. Create Production `.env` File

**Never commit this file to version control!**

```env
# =============================================================================
# DJANGO CORE
# =============================================================================
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<your-production-django-secret-64-chars>
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# =============================================================================
# DATABASE
# =============================================================================
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGODB_DB_NAME=verfai_production
MONGODB_REQUIRE_TLS=true

# =============================================================================
# JWT
# =============================================================================
JWT_SECRET_KEY=<your-production-jwt-secret-64-chars>
JWT_ACCESS_TOKEN_LIFETIME=900      # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# =============================================================================
# EMAIL
# =============================================================================
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# =============================================================================
# SECURITY
# =============================================================================
VALIDATE_SECURITY_CONFIG=true

# =============================================================================
# CORS
# =============================================================================
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# =============================================================================
# MODELS
# =============================================================================
LLM_WARMUP_ON_START=true

# =============================================================================
# RATE LIMITING (Production values - tighter than dev)
# =============================================================================
RATE_LIMIT_AUTH_LOGIN_REQUESTS=3
RATE_LIMIT_AUTH_LOGIN_WINDOW=300
RATE_LIMIT_AUTH_LOGIN_BLOCK=1800

RATE_LIMIT_AUTH_REGISTER_REQUESTS=2
RATE_LIMIT_AUTH_REGISTER_WINDOW=3600
RATE_LIMIT_AUTH_REGISTER_BLOCK=7200

```

---

## MongoDB Atlas Setup

### 1. Create MongoDB Atlas Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up or log in
3. Create new cluster:
   - **Tier**: M10 or higher (production)
   - **Region**: Closest to your app servers
   - **Cluster name**: `verif-ai-prod`

### 2. Configure Database Access

1. **Database Access** → **Add New Database User**
   - Username: `verfai-app`
   - Password: Generate strong password (save in secrets vault)
   - Database User Privileges: `readWrite` on `verfai_production`

### 3. Configure Network Access

#### IP Whitelist Configuration

**IMPORTANT:** Restrict MongoDB access to known IP addresses for security.

1. **Network Access** → **Add IP Address**

**Recommended Approach - Whitelist Specific IPs:**

| Environment | IP Address | Description | Status |
|-------------|------------|-------------|--------|
| **Production** | `[YOUR_SERVER_IP]` | Production application server | ⚠️ Configure |
| **Staging** | `[YOUR_STAGING_IP]` | Staging environment server | ⚠️ Configure |
| **CI/CD** | `[YOUR_CI_IP]` | GitHub Actions/Jenkins runner | Optional |
| **Development** | `[YOUR_DEV_IP]` | Developer machine (temporary) | Temporary only |

**Example Configuration:**
```
Production Server:    52.12.34.56/32     (AWS EC2 us-west-2)
Staging Server:       192.0.2.100/32     (Azure westus)
Office Network:       203.0.113.0/24     (Company VPN)
Developer (Temp):     198.51.100.45/32   (Home IP - expires in 7 days)
```

**Security Best Practices:**

✅ **DO:**
- Use specific IP addresses (`/32` CIDR for single IPs)
- Document each IP with purpose and expiration
- Use VPC peering for cloud deployments (AWS, Azure, GCP)
- Set temporary IPs with expiration dates
- Remove developer IPs after development
- Use corporate VPN IPs for office access
- Audit IP whitelist monthly

❌ **DON'T:**
- Use `0.0.0.0/0` (allows access from anywhere) in production
- Whitelist public Wi-Fi or shared networks
- Leave temporary developer IPs indefinitely
- Share credentials with whitelisted IPs

**For Local Development ONLY:**
- `0.0.0.0/0` - Allow access from anywhere
- ⚠️ **NEVER use in production!**
- Remove before deployment

**Cloud-Specific Recommendations:**

**AWS:**
```
Use VPC Peering:
1. MongoDB Atlas → Network Access → Peering
2. Select AWS region matching your EC2 instances
3. Configure VPC peering connection
4. No public IP whitelist needed
```

**Azure:**
```
Use Private Endpoint:
1. MongoDB Atlas → Network Access → Private Endpoint
2. Select Azure region
3. Configure Azure Private Link
```

**Google Cloud:**
```
Use Private Service Connect:
1. MongoDB Atlas → Network Access → Private Endpoint
2. Select GCP region
3. Configure endpoints
```

**IP Whitelist Update Procedure:**

1. **Adding New IP:**
   - Document purpose and owner
   - Set expiration date (if temporary)
   - Notify team via Slack/email
   - Update this documentation

2. **Removing IP:**
   - Verify IP is no longer needed
   - Notify affected parties 24h in advance
   - Remove from MongoDB Atlas
   - Update documentation

3. **Emergency Access:**
   - Contact MongoDB Atlas support
   - Temporary IP can be added within 5 minutes
   - Must provide business justification
   - Auto-expires in 24 hours

**Current IP Whitelist (Update Regularly):**

```markdown
Last Updated: [DATE]

Production IPs:
- [IP_ADDRESS] - [DESCRIPTION] - Added: [DATE] - Owner: [NAME]

Staging IPs:
- [IP_ADDRESS] - [DESCRIPTION] - Added: [DATE] - Owner: [NAME]

Temporary IPs:
- [IP_ADDRESS] - [DESCRIPTION] - Added: [DATE] - Expires: [DATE] - Owner: [NAME]
```

**Monitoring:**
- Enable MongoDB Atlas alerts for unauthorized access attempts
- Review access logs weekly
- Audit IP whitelist monthly
- Remove stale temporary IPs

**Alternative - For Local/Development Only:**
   - ⚠️ Use `0.0.0.0/0` (allow all) **ONLY for local development**
   - **Never use in production!**
   - Switch to IP whitelist or VPC peering for production

### 4. Get Connection String

1. **Databases** → **Connect** → **Connect your application**
2. Driver: Python, Version 3.10 or later
3. Copy connection string:
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/
   ```
4. Replace `<username>` and `<password>` with your credentials
5. Set as `MONGODB_URI` in environment

### 5. Enable Encryption at Rest

1. **Security** → **Encryption at Rest**
2. Enable for production deployments
3. Choose your cloud provider's KMS

### 6. Configure Backups

1. **Backup** → Enable continuous backup
2. Retention: 7-30 days
3. Test restore procedure

---

## Email Service Setup

### SendGrid Setup (Recommended)

#### 1. Create SendGrid Account

1. Sign up at [SendGrid](https://sendgrid.com)
2. Verify your email
3. Complete sender verification

#### 2. Create API Key

1. **Settings** → **API Keys** → **Create API Key**
2. Name: `verif-ai-production`
3. Permissions: **Mail Send** (full access)
4. Copy API key (shown only once!)
5. Set as `SENDGRID_API_KEY` in environment

#### 3. Verify Sender Domain

**Option 1: Domain Authentication (Recommended)**
1. **Settings** → **Sender Authentication** → **Authenticate Your Domain**
2. Add DNS records to your domain
3. Verify DNS propagation

**Option 2: Single Sender Verification**
1. **Settings** → **Sender Authentication** → **Single Sender Verification**
2. Enter email address (e.g., `noreply@yourdomain.com`)
3. Verify email

#### 4. Configure Sending

Set in `.env`:
```env
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=SG.your-api-key-here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

---

### Alternative: SMTP Setup

If using custom SMTP server:

```env
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
```

**Gmail Example:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=yourapp@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Generate App Password if 2FA enabled
EMAIL_USE_TLS=True
```

---

## Application Deployment

### Option 1: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "verfai.wsgi:application"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### 3. Build and Run

```bash
# Build image
docker build -t verif-ai-backend:latest .

# Run container
docker run -d \
  --name verif-ai-backend \
  --env-file .env \
  -p 8000:8000 \
  verif-ai-backend:latest
```

---

### Option 2: Kubernetes Deployment

#### 1. Create ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: verif-ai-config
data:
  DJANGO_DEBUG: "false"
  MONGODB_DB_NAME: "verfai_production"
  EMAIL_BACKEND: "sendgrid"
```

#### 2. Create Secrets

```bash
# Create from .env file
kubectl create secret generic verif-ai-secrets --from-env-file=.env
```

#### 3. Create Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: verif-ai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: verif-ai-backend
  template:
    metadata:
      labels:
        app: verif-ai-backend
    spec:
      containers:
      - name: backend
        image: verif-ai-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: verif-ai-config
        - secretRef:
            name: verif-ai-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

#### 4. Create Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: verif-ai-backend-service
spec:
  selector:
    app: verif-ai-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

### Option 3: Platform-as-a-Service (Heroku, Railway, Render)

#### Heroku Example

1. **Create app:**
   ```bash
   heroku create verif-ai-prod
   ```

2. **Set environment variables:**
   ```bash
   heroku config:set DJANGO_SECRET_KEY="your-secret"
   heroku config:set JWT_SECRET_KEY="your-jwt-secret"
   heroku config:set MONGODB_URI="mongodb+srv://..."
   # ... set all environment variables
   ```

3. **Create Procfile:**
   ```
   web: gunicorn --chdir backend verfai.wsgi:application
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   ```

---

## Post-Deployment

### 1. Database Initialization

```bash
# Run migrations (if using Django models)
python manage.py migrate

# Create initial roles and permissions
python manage.py seed_roles

# Verify database connection
python manage.py check_mongo
```

### 2. Create Admin User

```bash
python manage.py createsuperuser
```

Or programmatically:
```python
from src.domain.entities import User
from src.infrastructure.mongodb.repositories import MongoDBUserRepository
from src.domain.services import BCryptPasswordHasher

# Create admin user
user = User(
    email="admin@yourdomain.com",
    password_hash=BCryptPasswordHasher().hash_password("SecureAdminPass123!"),
    username="admin",
    roles=["admin"],
    is_active=True,
    is_verified=True
)

# Save to database
repo = MongoDBUserRepository(client, db_name)
repo.create_user(user)
```

### 3. Verify Deployment

```bash
# Health check
curl https://yourdomain.com/api/health

# Expected response:
# {"status": "healthy", "database": "connected", ...}

# MongoDB health
curl https://yourdomain.com/api/health/mongodb

# Test authentication
curl -X POST https://yourdomain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"TestPass123!"}'
```

### 4. Configure SSL/TLS

#### Using Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### Using Cloudflare

1. Add domain to Cloudflare
2. Enable Full (Strict) SSL/TLS mode
3. Update DNS records
4. Enable HSTS

### 5. Configure Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
```

---

## Monitoring & Maintenance

### 1. Logging

**File Logs:**
- Location: `backend/logs/`
- Files:
  - `security.log` - Security events (10MB rotate, 5 backups)
  - `django.log` - Application logs

**MongoDB Audit Logs:**
- Collection: `audit_logs`
- TTL: 90 days (auto-cleanup)
- Query examples:
  ```javascript
  // Failed logins in last 24 hours
  db.audit_logs.find({
    event_type: "auth.login.failed",
    timestamp: { $gte: new Date(Date.now() - 24*60*60*1000) }
  }).sort({ timestamp: -1 })
  
  // Admin actions
  db.audit_logs.find({
    event_type: { $regex: /^authz|admin/ }
  }).sort({ timestamp: -1 }).limit(100)
  ```

### 2. Monitoring Endpoints

```bash
# System health
GET /api/health/

# Database health
GET /api/health/mongodb/

# Admin metrics (requires admin auth)
GET /api/admin/model-health/
GET /api/admin/analysis-stats/
GET /api/admin/user-stats/
```

### 3. Alerting

Set up alerts for:
- **High error rates** (>1% of requests)
- **Failed login spikes** (>10 in 5 minutes)
- **Database connection failures**
- **High memory/CPU usage** (>80%)
- **Slow response times** (>1 second)
- **Rate limit exceeded** (multiple IPs)

### 4. Backups

**MongoDB Atlas (Automated):**
- Continuous backups enabled
- Point-in-time recovery
- 7-30 day retention

**Manual Backup:**
```bash
# Export database
mongodump --uri="mongodb+srv://..." --db=verfai_production --out=backup/

# Import backup
mongorestore --uri="mongodb+srv://..." --db=verfai_production backup/verfai_production/
```

### 5. Updates & Maintenance

**Regular Tasks:**
- [ ] Update dependencies monthly
- [ ] Review security logs weekly
- [ ] Rotate secrets quarterly
- [ ] Test backups monthly
- [ ] Review audit logs weekly
- [ ] Update SSL certificates (auto with certbot)

**Update Process:**
```bash
# 1. Pull latest code
git pull origin main

# 2. Update dependencies
pip install -r backend/requirements.txt --upgrade

# 3. Run tests
pytest backend/tests/

# 4. Deploy
# (Use your deployment method)

# 5. Verify
curl https://yourdomain.com/api/health
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start

**Symptoms:** Container/process crashes on startup

**Checks:**
1. Environment variables set correctly
2. MongoDB connection string valid
3. MongoDB IP whitelisted
4. Secrets are long enough
5. Check logs: `docker logs container-name`

**Solutions:**
```bash
# Verify environment
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env'); print(os.getenv('MONGODB_URI'))"

# Test MongoDB connection
python backend/manage.py check_mongo

# Validate security config
python backend/manage.py check
```

---

#### Database Connection Errors

**Error:** `ServerSelectionTimeoutError: No servers found`

**Causes:**
- MongoDB Atlas IP not whitelisted
- Incorrect connection string
- Network/firewall blocking connection

**Solutions:**
1. Verify IP whitelist in MongoDB Atlas
2. Test connection: `python backend/manage.py check_mongo`
3. Check firewall rules
4. Verify credentials in connection string

---

#### Email Not Sending

**Symptoms:** Verification emails not received

**Checks:**
1. `EMAIL_BACKEND` set correctly
2. SendGrid API key valid
3. Sender email verified
4. Check spam folder

**Debug:**
```python
# Test email configuration
from src.infrastructure.email_service import get_email_service

email_service = get_email_service()
result = email_service.send_verification_email("test@example.com", "test-token")
print(f"Email sent: {result}")
```

---

#### SSL/Certificate Errors

**Error:** `SSL certificate verification failed`

**Solutions:**
1. Verify SSL certificate is valid: `openssl s_client -connect yourdomain.com:443`
2. Check certbot renewal: `sudo certbot renew --dry-run`
3. Verify nginx configuration: `sudo nginx -t`
4. Restart nginx: `sudo systemctl restart nginx`

---

#### High Memory Usage

**Symptoms:** Server running out of memory

**Causes:**
- ML models loaded multiple times
- Memory leaks
- Insufficient resources

**Solutions:**
1. Enable model warmup: `LLM_WARMUP_ON_START=true`
2. Increase server memory (minimum 2GB recommended)
3. Monitor with: `docker stats` or `htop`
4. Set resource limits in Docker/Kubernetes

---

## Rollback Procedures

### 1. Quick Rollback (Docker)

```bash
# Stop current container
docker stop verif-ai-backend

# Run previous version
docker run -d \
  --name verif-ai-backend \
  --env-file .env \
  -p 8000:8000 \
  verif-ai-backend:previous-tag
```

### 2. Kubernetes Rollback

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/verif-ai-backend

# Rollback to specific revision
kubectl rollout undo deployment/verif-ai-backend --to-revision=2

# Check rollout status
kubectl rollout status deployment/verif-ai-backend
```

### 3. Database Rollback

```bash
# Restore from backup
mongorestore --uri="mongodb+srv://..." \
  --db=verfai_production \
  --drop \
  backup/verfai_production/
```

---

## Performance Optimization

### 1. Application Optimization

- Enable model warmup: `LLM_WARMUP_ON_START=true`
- Use gunicorn workers: `--workers 4`
- Enable keepalive: `--keep-alive 5`
- Increase timeout: `--timeout 120`

### 2. Database Optimization

- Create indexes on frequently queried fields
- Enable MongoDB profiling
- Monitor slow queries
- Implement caching (Redis)

### 3. Caching Strategy

```python
# Future enhancement: Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

---

## Security Hardening

### Production Security Checklist

- [ ] HTTPS enabled with valid certificate
- [ ] HSTS header enabled (31536000 seconds)
- [ ] Secure session cookies (HTTPS only)
- [ ] CSRF protection enabled
- [ ] XSS protection headers set
- [ ] Rate limiting configured
- [ ] Admin interface restricted
- [ ] Debug mode disabled
- [ ] Strong secrets (64+ characters)
- [ ] Database credentials rotated
- [ ] Audit logging enabled
- [ ] Security monitoring active
- [ ] Firewall configured
- [ ] Only necessary ports open
- [ ] Regular security updates scheduled

---

## Support & Resources

### Documentation
- [API Reference](API_REFERENCE.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Security Best Practices](SECURITY_BEST_PRACTICES.md)
- [Security Overview](SECURITY.md)

### External Resources
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)
- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Getting Help
- Check logs first: `docker logs container-name`
- Review error messages carefully
- Test components individually
- Consult documentation
- Contact development team

---

**Congratulations!** Your Verif-AI backend is now deployed to production. 🎉

Remember to:
- Monitor logs regularly
- Keep dependencies updated
- Review security regularly
- Test backups monthly
- Rotate secrets quarterly
