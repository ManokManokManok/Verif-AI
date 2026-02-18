# Security Best Practices Guide — Verif-AI

> Comprehensive security guidelines for developers and operators
> Last updated: February 18, 2026

---

## Table of Contents

- [Overview](#overview)
- [Authentication & Authorization](#authentication--authorization)
- [Input Validation](#input-validation)
- [Data Protection](#data-protection)
- [API Security](#api-security)
- [Database Security](#database-security)
- [Logging & Monitoring](#logging--monitoring)
- [Deployment Security](#deployment-security)
- [Incident Response](#incident-response)
- [Code Review Checklist](#code-review-checklist)

---

## Overview

This guide covers security best practices for developing, deploying, and operating Verif-AI. Following these guidelines helps protect against common vulnerabilities and ensures compliance with security standards.

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal access rights for users and services
3. **Fail Secure**: Default to deny, explicit allow
4. **Secure by Default**: Security enabled out of the box
5. **Audit Everything**: Comprehensive logging of security events

---

## Authentication & Authorization

### Password Management

#### ✅ DO

- **Use strong password hashing**
  ```python
  # BCrypt with 12+ rounds
  hasher = BCryptPasswordHasher(rounds=12)
  password_hash = hasher.hash_password(password)
  ```

- **Enforce strong password policies**
  - Minimum 8 characters
  - Require uppercase, lowercase, digit, special character
  - Maximum length to prevent DoS (128 chars)
  - No common passwords (e.g., "Password123!")

- **Implement password reset securely**
  - Use cryptographically secure tokens
  - Short expiration (1 hour)
  - Single-use tokens
  - Send via secure channel (email)

#### ❌ DON'T

- Never store passwords in plain text
- Never log passwords (even hashed)
- Never send passwords in URLs
- Never use weak hashing (MD5, SHA1)
- Never reuse password reset tokens

---

### JWT Token Security

#### ✅ DO

- **Use strong secrets**
  ```python
  # Generate 64+ character secrets
  import secrets
  jwt_secret = secrets.token_urlsafe(64)
  ```

- **Set appropriate token lifetimes**
  - Access tokens: 15-30 minutes
  - Refresh tokens: 7-30 days
  - Shorter is more secure

- **Validate all token claims**
  ```python
  # Check signature, expiry, issuer, audience
  payload = jwt_service.verify_access_token(token)
  ```

- **Implement token blacklisting**
  - Blacklist on logout
  - Blacklist on password change
  - Clean up expired entries

#### ❌ DON'T

- Never use algorithm "none"
- Never skip signature verification
- Never extend token expiry on refresh
- Never store sensitive data in tokens
- Never use same secret for different purposes

---

### Multi-Factor Authentication (MFA)

#### ✅ DO

- **Use cryptographically secure code generation**
  ```python
  code = MFACodeGenerator.generate_code(length=6)
  ```

- **Implement rate limiting**
  - Limit code send requests (3 per 5 min)
  - Limit verification attempts (5 per 5 min)
  - Block after too many failures

- **Set short expiration**
  - 5 minutes for email codes
  - 30 seconds for TOTP (future enhancement)

- **Limit verification attempts**
  - Maximum 3 attempts per code
  - Invalidate code after max attempts

#### ❌ DON'T

- Never use predictable codes (e.g., sequential)
- Never allow unlimited verification attempts
- Never log MFA codes
- Never send codes via SMS (less secure than email)

---

### Role-Based Access Control (RBAC)

#### ✅ DO

- **Follow principle of least privilege**
  ```python
  # Assign minimal necessary permissions
  default_user_permissions = [
      "view_profile",
      "update_profile",
      "analyze_content",
      "view_history"
  ]
  ```

- **Check permissions explicitly**
  ```python
  @require_permission('manage_users')
  def update_user_status(request, user_id):
      # ...
  ```

- **Validate resource ownership**
  ```python
  # Verify user owns the resource
  if resource.user_id != request.user_id:
      raise PermissionDenied()
  ```

#### ❌ DON'T

- Never grant admin by default
- Never skip permission checks
- Never rely only on client-side checks
- Never use hardcoded role names in business logic

---

## Input Validation

### Server-Side Validation

#### ✅ DO

- **Validate all inputs server-side**
  ```python
  validator = RequestValidator()
  validator.add_field('email', FieldType.EMAIL, required=True)
  is_valid, errors, cleaned = validator.validate(request.data)
  ```

- **Use allowlists over denylists**
  ```python
  # Good: Explicit allowed characters
  pattern = r'^[a-zA-Z0-9_-]+$'
  
  # Bad: Blacklist approach
  if '<script>' in input:  # Can be bypassed
  ```

- **Sanitize output for display**
  ```python
  import html
  safe_text = html.escape(user_input, quote=True)
  ```

- **Enforce length limits**
  ```python
  # Prevent DoS via large inputs
  MAX_MESSAGE_LENGTH = 10000  # 10KB
  MAX_EMAIL_LENGTH = 254
  MAX_PASSWORD_LENGTH = 128  # Prevent bcrypt DoS
  ```

#### ❌ DON'T

- Never trust client-side validation alone
- Never concatenate user input into queries
- Never allow arbitrary HTML without sanitization
- Never skip validation on "trusted" endpoints

---

### SQL/NoSQL Injection Prevention

#### ✅ DO

- **Use parameterized queries**
  ```python
  # MongoDB - Good
  db.users.find({"email": user_email})
  
  # SQL - Good
  cursor.execute("SELECT * FROM users WHERE email = %s", [email])
  ```

- **Validate and sanitize search inputs**
  ```python
  # Escape special characters
  search = sanitize_for_logging(search_query)
  ```

#### ❌ DON'T

- **Never concatenate user input**
  ```python
  # MongoDB - BAD
  db.users.find({"email": f"{user_input}"})
  
  # SQL - BAD
  query = f"SELECT * FROM users WHERE email = '{email}'"
  ```

---

### XSS Prevention

#### ✅ DO

- **Escape HTML entities**
  ```python
  import html
  safe_html = html.escape(user_content, quote=True)
  ```

- **Use Content Security Policy (CSP)**
  ```python
  # In settings.py
  SECURE_CONTENT_TYPE_NOSNIFF = True
  SECURE_BROWSER_XSS_FILTER = True
  X_FRAME_OPTIONS = 'DENY'
  ```

- **Validate URLs**
  ```python
  from urllib.parse import urlparse
  
  parsed = urlparse(user_url)
  if parsed.scheme not in ['http', 'https']:
      raise ValidationError("Invalid URL scheme")
  ```

#### ❌ DON'T

- Never render user input as HTML without escaping
- Never use `innerHTML` with user content
- Never trust user-provided URLs
- Never disable XSS filters

---

## Data Protection

### Sensitive Data Handling

#### ✅ DO

- **Encrypt sensitive data at rest**
  - Use MongoDB Atlas encryption
  - Encrypt backups
  - Protect encryption keys

- **Use TLS/SSL for data in transit**
  ```python
  # Enforce TLS for MongoDB
  MONGODB_REQUIRE_TLS=true
  
  # HTTPS only in production
  SECURE_SSL_REDIRECT = True
  ```

- **Minimize sensitive data storage**
  - Don't store unnecessary PII
  - Hash/tokenize when possible
  - Implement data retention policies

- **Redact sensitive data in logs**
  ```python
  # Good
  logger.info(f"Login attempt for user: {sanitize_for_logging(email)}")
  
  # Bad
  logger.info(f"Login with password: {password}")
  ```

#### ❌ DON'T

- Never log passwords, tokens, or keys
- Never store sensitive data in plain text
- Never expose sensitive data in URLs
- Never include sensitive data in error messages

---

### Database Security

#### ✅ DO

- **Use strong credentials**
  - Long, random passwords
  - Rotate credentials regularly
  - Use separate accounts for dev/prod

- **Implement proper access control**
  - Principle of least privilege
  - Separate read/write permissions
  - No shared accounts

- **Enable audit logging**
  ```python
  # Log all database operations
  audit_logger.log_event(
      AuditEventType.USER_DELETED,
      user_id=user_id,
      action="delete_user"
  )
  ```

- **Backup regularly**
  - Automated daily backups
  - Test restore procedures
  - Encrypt backup files

#### ❌ DON'T

- Never use default credentials
- Never disable authentication
- Never run as root/admin
- Never store credentials in code

---

## API Security

### Rate Limiting

#### ✅ DO

- **Implement aggressive rate limits on auth endpoints**
  ```python
  # Login: 5 requests per 5 minutes
  RATE_LIMIT_AUTH_LOGIN_REQUESTS=5
  RATE_LIMIT_AUTH_LOGIN_WINDOW=300
  ```

- **Use progressive rate limiting**
  - Stricter limits for unauthenticated users
  - Per-user limits for authenticated requests
  - IP-based limits as backup

- **Return proper headers**
  ```python
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1676721600
  ```

#### ❌ DON'T

- Never allow unlimited requests
- Never use only client-side throttling
- Never forget about retry-after headers

---

### CORS Configuration

#### ✅ DO

- **Explicitly allow origins**
  ```python
  CORS_ALLOWED_ORIGINS = [
      'https://verif-ai.com',
      'https://www.verif-ai.com'
  ]
  ```

- **Use credentials carefully**
  ```python
  CORS_ALLOW_CREDENTIALS = True  # Only if needed
  ```

#### ❌ DON'T

- Never use `*` wildcard with credentials
- Never allow all origins in production
- Never trust Origin header alone

---

### CSRF Protection

#### ✅ DO

- **Enable CSRF middleware**
  ```python
  MIDDLEWARE = [
      'django.middleware.csrf.CsrfViewMiddleware',
  ]
  ```

- **Use CSRF tokens in forms**
  ```html
  <form method="post">
    {% csrf_token %}
    <!-- form fields -->
  </form>
  ```

#### ❌ DON'T

- Never disable CSRF for convenience
- Never exempt views unnecessarily
- Never use GET for state-changing operations

---

## Logging & Monitoring

### Security Logging

#### ✅ DO

- **Log all security events**
  ```python
  audit_logger.log_event(
      AuditEventType.LOGIN_FAILED,
      user_id=user_id,
      ip_address=get_client_ip(request),
      user_agent=request.META.get('HTTP_USER_AGENT'),
      error_message="Invalid credentials"
  )
  ```

- **Include context in logs**
  - Timestamp (UTC)
  - User ID (if authenticated)
  - IP address
  - User agent
  - Action performed
  - Result (success/failure)

- **Implement log rotation**
  ```python
  'security_file': {
      'class': 'logging.handlers.RotatingFileHandler',
      'maxBytes': 10485760,  # 10MB
      'backupCount': 5,
  }
  ```

- **Monitor for suspicious patterns**
  - Multiple failed logins
  - Unusual access patterns
  - Permission denied attempts
  - Rate limit violations

#### ❌ DON'T

- Never log sensitive data
- Never log to user-accessible locations
- Never trust log injection inputs
- Never ignore log anomalies

---

### Audit Trail

#### ✅ DO

- **Log critical operations**
  - User creation/deletion
  - Password changes
  - Role assignments
  - Permission changes
  - Admin actions

- **Make logs tamper-evident**
  - Store in append-only location
  - Hash log entries
  - Use external log aggregation
  - Implement retention policies

- **Review logs regularly**
  - Automated alerts for anomalies
  - Manual security reviews
  - Compliance audits

---

## Deployment Security

### Production Checklist

#### ✅ DO

- **Environment Configuration**
  - [ ] `DJANGO_DEBUG=false`
  - [ ] Strong `DJANGO_SECRET_KEY` (64+ chars)
  - [ ] Strong `JWT_SECRET_KEY` (64+ chars, different from Django)
  - [ ] `VALIDATE_SECURITY_CONFIG=true`
  - [ ] Proper `DJANGO_ALLOWED_HOSTS`
  - [ ] Restrictive `CORS_ALLOWED_ORIGINS`

- **HTTPS Configuration**
  - [ ] SSL/TLS certificate installed
  - [ ] HSTS enabled (`SECURE_HSTS_SECONDS=31536000`)
  - [ ] Force HTTPS (`SECURE_SSL_REDIRECT=True`)
  - [ ] Secure cookies enabled

- **Database Security**
  - [ ] Use strong credentials
  - [ ] Enable TLS/SSL
  - [ ] Restrict network access
  - [ ] Enable audit logging

- **Secrets Management**
  - [ ] Use environment variables
  - [ ] Never commit secrets
  - [ ] Rotate keys regularly
  - [ ] Use secret management service (AWS Secrets Manager, etc.)

#### ❌ DON'T

- Never deploy with `DEBUG=true`
- Never use weak secrets
- Never expose admin interface publicly
- Never run as root
- Never skip security updates

---

### Container Security

#### ✅ DO

- **Use minimal base images**
  ```dockerfile
  FROM python:3.10-slim
  ```

- **Run as non-root user**
  ```dockerfile
  USER appuser
  ```

- **Scan for vulnerabilities**
  ```bash
  docker scan your-image:tag
  ```

- **Use health checks**
  ```dockerfile
  HEALTHCHECK CMD curl -f http://localhost:8000/api/health || exit 1
  ```

---

## Incident Response

### Security Incident Response Plan

#### 1. Detection
- Monitor logs for anomalies
- Alert on suspicious patterns
- User reports

#### 2. Containment
- Isolate affected systems
- Block malicious IPs
- Revoke compromised credentials

#### 3. Investigation
- Analyze logs
- Identify attack vector
- Determine scope of impact

#### 4. Recovery
- Patch vulnerabilities
- Restore from clean backups
- Reset affected credentials

#### 5. Post-Incident
- Document findings
- Update security measures
- Notify affected users
- Review and improve

---

### Vulnerability Disclosure

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email security contact directly
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
4. Allow 48 hours for initial response
5. Give reasonable time for fix (coordinated disclosure)

---

## Code Review Checklist

### Authentication & Authorization
- [ ] User inputs are validated server-side
- [ ] Passwords are hashed with bcrypt (12+ rounds)
- [ ] JWT tokens are validated completely
- [ ] Permission checks are enforced
- [ ] Rate limiting is applied
- [ ] MFA is implemented for sensitive operations

### Input Validation
- [ ] All user inputs are validated
- [ ] Parameterized queries are used
- [ ] HTML is escaped for output
- [ ] File uploads are validated (type, size)
- [ ] Length limits are enforced

### Data Protection
- [ ] Sensitive data is encrypted
- [ ] TLS/SSL is enforced
- [ ] Secrets are not in code
- [ ] Logs don't contain sensitive data

### Error Handling
- [ ] Generic error messages for users
- [ ] Detailed logs for debugging
- [ ] No stack traces in production
- [ ] Security exceptions are logged

### API Security
- [ ] CORS is properly configured
- [ ] CSRF protection is enabled
- [ ] Rate limiting is implemented
- [ ] Authentication is required

---

## Security Testing

### Manual Testing

- **Authentication testing**
  - Weak password attempts
  - Brute force attacks
  - Session fixation
  - Token manipulation

- **Authorization testing**
  - Privilege escalation
  - Horizontal access control
  - Resource access without auth

- **Input validation**
  - SQL injection
  - NoSQL injection
  - XSS attacks
  - Path traversal

### Automated Testing

```python
# Run security tests
pytest backend/tests/test_admin_security.py
pytest backend/tests/test_api_security.py

# Check for known vulnerabilities
pip-audit

# Static analysis
bandit -r backend/src/
```

---

## Resources

### OWASP References
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

### Standards
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls)
- [PCI DSS](https://www.pcisecuritystandards.org/)

### Tools
- [Bandit](https://github.com/PyCQA/bandit) - Python security linter
- [Safety](https://github.com/pyupio/safety) - Dependency vulnerability scanner
- [OWASP ZAP](https://www.zaproxy.org/) - Security testing

---

## Compliance

### Data Privacy
- Implement data retention policies
- Provide data export/deletion
- Document data processing
- Obtain proper consent

### Audit Requirements
- Maintain audit logs for 90 days minimum
- Include user actions, admin actions, security events
- Protect log integrity
- Regular log reviews

---

For specific implementation details, see:
- [API Reference](API_REFERENCE.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Security Overview](SECURITY.md)
- [Deployment Guide](DEPLOYMENT.md)
