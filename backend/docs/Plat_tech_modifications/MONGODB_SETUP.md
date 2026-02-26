# MongoDB Atlas Setup Guide

## Role-Based Access Control (Least Privilege Principle)

This guide explains how to configure MongoDB Atlas users with least privilege access for enhanced security.

---

## 🎯 Overview

Verif-AI implements role-based access control for MongoDB to follow the **least privilege principle**:

| Role | Permissions | Use Case | Environment Variable |
|------|-------------|----------|---------------------|
| **Backend** | readWrite on `verfai` database | Main application operations | `MONGODB_URI_BACKEND` |
| **Analytics** | read on `verfai` database | Reporting, dashboards, analytics | `MONGODB_URI_ANALYTICS` |
| **Admin** | dbAdmin on `verfai` database | Migrations, schema changes, maintenance | `MONGODB_URI_ADMIN` |

**Security Benefits:**
- 🛡️ **Defense in Depth**: Credential compromise limited to one role
- 📊 **Read-Only Safety**: Analytics queries cannot modify data
- 🔒 **Audit Trail**: Admin operations isolated and traceable
- ⚡ **Blast Radius Reduction**: One compromised credential ≠ full database access

---

## 📋 Prerequisites

- MongoDB Atlas account
- Existing cluster with `verfai` database
- Atlas project with appropriate permissions (Project Owner or Database Access Manager)

---

## 🔧 Step 1: Create MongoDB Atlas Users

### 1.1 Access Database Access Settings

1. Log in to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Navigate to your project
3. Click **Database Access** in the left sidebar
4. Click **Add New Database User**

### 1.2 Create Backend User (Read/Write Access)

**Configuration:**
```
Username: verfai-backend
Password: [Generate strong password - save to password manager]

Database User Privileges:
- Database: verfai
- Role: readWrite

Built-In Role: readWrite
```

**Steps:**
1. Click **Add New Database User**
2. Authentication Method: **Password**
3. Username: `verfai-backend`
4. Password: Click **Autogenerate Secure Password** (save it!)
5. Database User Privileges: Select **Custom Roles**
6. Add Custom Role:
   - Database: `verfai`
   - Collection: (leave empty for all collections)
   - Role: `readWrite`
7. Click **Add User**

**Connection String:**
```
mongodb+srv://verfai-backend:<password>@cluster0.mongodb.net/
```

### 1.3 Create Analytics User (Read-Only Access)

**Configuration:**
```
Username: verfai-analytics
Password: [Generate strong password - save to password manager]

Database User Privileges:
- Database: verfai
- Role: read

Built-In Role: read
```

**Steps:**
1. Click **Add New Database User**
2. Authentication Method: **Password**
3. Username: `verfai-analytics`
4. Password: Click **Autogenerate Secure Password** (save it!)
5. Database User Privileges: Select **Custom Roles**
6. Add Custom Role:
   - Database: `verfai`
   - Collection: (leave empty)
   - Role: `read`
7. Click **Add User**

**Connection String:**
```
mongodb+srv://verfai-analytics:<password>@cluster0.mongodb.net/
```

### 1.4 Create Admin User (Database Administration)

**Configuration:**
```
Username: verfai-admin
Password: [Generate strong password - save to password manager]

Database User Privileges:
- Database: verfai
- Role: dbAdmin

Built-In Role: dbAdmin
```

**Steps:**
1. Click **Add New Database User**
2. Authentication Method: **Password**
3. Username: `verfai-admin`
4. Password: Click **Autogenerate Secure Password** (save it!)
5. Database User Privileges: Select **Custom Roles**
6. Add Custom Role:
   - Database: `verfai`
   - Collection: (leave empty)
   - Role: `dbAdmin`
7. Click **Add User**

**Connection String:**
```
mongodb+srv://verfai-admin:<password>@cluster0.mongodb.net/
```

---

## ⚙️ Step 2: Update Environment Variables

### 2.1 Update `.env` File

Add the role-specific connection strings to your `.env` file:

```dotenv
# =============================================================================
# MongoDB Atlas - Role-Based Access
# =============================================================================

# Backend User (readWrite permissions)
MONGODB_URI_BACKEND=mongodb+srv://verfai-backend:<backend-password>@cluster0.mongodb.net/

# Analytics User (read-only permissions)
MONGODB_URI_ANALYTICS=mongodb+srv://verfai-analytics:<analytics-password>@cluster0.mongodb.net/

# Admin User (dbAdmin permissions)
MONGODB_URI_ADMIN=mongodb+srv://verfai-admin:<admin-password>@cluster0.mongodb.net/

# Database name
MONGODB_DB_NAME=verfai

# Legacy fallback (optional - uses backend URI if not set)
MONGODB_URI=mongodb+srv://verfai-backend:<backend-password>@cluster0.mongodb.net/
```

**Replace `<password>` placeholders with actual passwords from Step 1!**

### 2.2 Verify Environment Variables

```powershell
# Check environment variables are set (passwords will be hidden in output)
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('BACKEND:', 'SET' if os.getenv('MONGODB_URI_BACKEND') else 'MISSING'); print('ANALYTICS:', 'SET' if os.getenv('MONGODB_URI_ANALYTICS') else 'MISSING'); print('ADMIN:', 'SET' if os.getenv('MONGODB_URI_ADMIN') else 'MISSING')"
```

**Expected Output:**
```
BACKEND: SET
ANALYTICS: SET
ADMIN: SET
```

---

## 🧪 Step 3: Test Role-Based Access

### 3.1 Run Unit Tests

```powershell
cd backend
python -m pytest tests/test_mongodb_security.py -v
```

**Expected Output:**
```
tests/test_mongodb_security.py::TestTLSEnforcement::test_is_remote_uri_atlas PASSED
tests/test_mongodb_security.py::TestRoleBasedAccess::test_get_backend_client PASSED
tests/test_mongodb_security.py::TestRoleBasedAccess::test_get_analytics_client PASSED
...
======================== 25 passed in 0.15s ========================
```

### 3.2 Test Analytics Read-Only Access (Manual)

Create a test script `test_analytics_readonly.py`:

```python
"""
Test script to verify analytics user cannot write to database.
This should FAIL with OperationFailure if permissions are correct.
"""
from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name
from pymongo.errors import OperationFailure

client = get_mongo_client(role='analytics')
db = client[get_database_name()]

try:
    # Attempt to insert (should fail)
    result = db['test_collection'].insert_one({'test': 'data'})
    print('❌ SECURITY ISSUE: Analytics user can write to database!')
    print(f'   Inserted document: {result.inserted_id}')
except OperationFailure as e:
    print('✅ CORRECT: Analytics user cannot write to database')
    print(f'   Error: {e}')
```

Run the test:
```powershell
python test_analytics_readonly.py
```

**Expected Output:**
```
✅ CORRECT: Analytics user cannot write to database
   Error: not authorized on verfai to execute command...
```

### 3.3 Test Backend Write Access

Create a test script `test_backend_write.py`:

```python
"""
Test script to verify backend user can write to database.
"""
from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name

client = get_mongo_client(role='backend')
db = client[get_database_name()]

try:
    # Insert test document
    result = db['test_collection'].insert_one({'test': 'write_test', 'role': 'backend'})
    print(f'✅ Backend user can write: Inserted {result.inserted_id}')
    
    # Clean up
    db['test_collection'].delete_one({'_id': result.inserted_id})
    print('✅ Cleanup successful')
except Exception as e:
    print(f'❌ Backend user cannot write: {e}')
```

Run the test:
```powershell
python test_backend_write.py
```

**Expected Output:**
```
✅ Backend user can write: Inserted 507f1f77bcf86cd799439011
✅ Cleanup successful
```

---

## 📖 Step 4: Update Application Code (If Needed)

### 4.1 Using Role-Based Connections

**Default behavior (backend role):**
```python
from src.infrastructure.mongodb.connection import get_mongo_client, get_database

# Uses MONGODB_URI_BACKEND or falls back to MONGODB_URI
client = get_mongo_client()
db = get_database()
```

**Analytics queries (read-only):**
```python
from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name

# Uses MONGODB_URI_ANALYTICS
client = get_mongo_client(role='analytics')
db = client[get_database_name()]

# Safe to run expensive queries - cannot modify data
results = db['verifications'].aggregate([...])
```

**Admin operations (migrations, indexes):**
```python
from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name

# Uses MONGODB_URI_ADMIN
client = get_mongo_client(role='admin')
db = client[get_database_name()]

# Can create indexes, modify schema
db['verifications'].create_index('created_at')
```

### 4.2 Backward Compatibility

If role-specific URIs are not set, the application falls back to `MONGODB_URI`:

```python
# If MONGODB_URI_BACKEND is not set, uses MONGODB_URI
client = get_mongo_client(role='backend')  # Works even without MONGODB_URI_BACKEND
```

**No code changes required for existing functionality!**

---

## 🔒 Security Best Practices

### Password Management

✅ **DO:**
- Use MongoDB Atlas auto-generated passwords (32+ characters)
- Store passwords in a secure password manager (1Password, LastPass, etc.)
- Rotate passwords every 90 days
- Use different passwords for each role

❌ **DON'T:**
- Use weak passwords (<20 characters)
- Share passwords between roles
- Store passwords in version control
- Email passwords in plain text

### Network Security

1. **IP Whitelist** (MongoDB Atlas Network Access):
   ```
   Production: 52.12.34.56 (AWS EC2)
   Staging: 192.0.2.100 (Staging server)
   Development: [Your IP] (temporary)
   ```

2. **Avoid `0.0.0.0/0`** (allow all):
   - Only use during initial development
   - Remove before production deployment

### Credential Rotation

**Quarterly rotation procedure:**

1. Create new user with same permissions (e.g., `verfai-backend-q1-2026`)
2. Update `.env` with new connection string
3. Deploy and verify application works
4. Delete old user in MongoDB Atlas
5. Update password manager

---

## 🐛 Troubleshooting

### Issue: "MONGODB_URI_BACKEND is not set"

**Cause:** Environment variable not loaded

**Solution:**
```powershell
# Verify .env file exists
ls .env

# Check if variable is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('MONGODB_URI_BACKEND'))"
```

### Issue: "not authorized on verfai to execute command"

**Cause:** User permissions incorrect

**Solution:**
1. Check MongoDB Atlas Database Access
2. Verify user has correct role on `verfai` database
3. Ensure role is `readWrite` (backend), `read` (analytics), or `dbAdmin` (admin)

### Issue: "Authentication failed"

**Cause:** Incorrect password in connection string

**Solution:**
1. Reset password in MongoDB Atlas
2. Update `.env` file with new password
3. Ensure special characters in password are URL-encoded:
   - `@` → `%40`
   - `:` → `%3A`
   - `#` → `%23`

### Issue: Connection timeout

**Cause:** IP not whitelisted in MongoDB Atlas

**Solution:**
1. Go to MongoDB Atlas → Network Access
2. Add your current IP address
3. Wait 2-3 minutes for changes to propagate

---

## 📊 Verification Checklist

After completing setup, verify:

- [ ] Three MongoDB Atlas users created (backend, analytics, admin)
- [ ] Backend user has `readWrite` role on `verfai` database
- [ ] Analytics user has `read` role on `verfai` database
- [ ] Admin user has `dbAdmin` role on `verfai` database
- [ ] `.env` file contains all three connection strings
- [ ] Passwords stored in secure password manager
- [ ] Unit tests passing: `pytest tests/test_mongodb_security.py`
- [ ] Analytics user **cannot** write (test script confirms)
- [ ] Backend user **can** write (test script confirms)
- [ ] IP whitelist configured for production environment
- [ ] No `0.0.0.0/0` in production IP whitelist
- [ ] Passwords not committed to version control

---

## 📚 Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [MongoDB Built-In Roles](https://www.mongodb.com/docs/manual/reference/built-in-roles/)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)
- [Verif-AI Security Best Practices](SECURITY_BEST_PRACTICES.md)

---

## 🆘 Support

For security questions:
- **Email:** security@verif-ai.example.com
- **Documentation:** [SECURITY.md](SECURITY.md)
- **Do NOT** open public GitHub issues for security vulnerabilities
