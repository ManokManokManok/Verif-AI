# Authentication & RBAC Implementation Plan

## 1. Goals

- Implement **email + password authentication**
- Use **JWT-based stateless auth**
- Apply **Role-Based Access Control (RBAC)**
- Keep **domain and use cases framework-agnostic**
- Use **MongoDB as source of truth for users**
- Use **Django only as an interface/adaptor**

---

## 2. Architectural Principles

- **Dependency Rule**: Outer layers depend on inner layers only
- **No Django imports in domain or use cases**
- **Business logic lives in use cases**
- **Framework logic lives in interfaces & infrastructure**

---

## 3. High-Level Flow

### Sign-Up
1. Client sends email + password
2. Django REST interface parses request
3. Signup use case executes business rules
4. User saved in MongoDB with default role
5. User data returned (no password)

### Sign-In
1. Client sends email + password
2. Use case validates credentials
3. JWT access (and refresh) tokens generated with roles
4. Tokens returned to client

### Authenticated Request
1. Client sends JWT in `Authorization` header
2. Django middleware validates token
3. User ID and roles attached to request context
4. RBAC middleware checks permissions

---

## 4. Security Enhancements

### Password Security
- **Password hashing**: Use `bcrypt` instead of storing plaintext
- **Password strength validation**: Minimum length, complexity requirements
- **Password reset flow**: Secure token-based password reset

### JWT Security
- **Short-lived access tokens**: 15-30 minutes expiry
- **Refresh token rotation**: Invalidate old refresh tokens when issuing new ones
- **Token blacklisting**: Store revoked tokens in Redis/MongoDB for logout
- **Secure token storage**: HttpOnly, SameSite cookies for refresh tokens

### Additional Security
- **Email verification**: Account verification on signup
- **Rate limiting**: Prevent brute force attacks on auth endpoints
- **Input validation**: Comprehensive validation for email format, password requirements

---

## 5. Domain Layer Design

### Core Entities
```python
# src/domain/entities.py
class Role:
    id: str
    name: str  # 'admin', 'moderator', 'user'
    permissions: List[str]
    description: str

class User:
    id: str
    email: str
    password_hash: str
    roles: List[str]  # Role IDs
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime

class Permission:
    id: str
    name: str  # 'create_post', 'delete_user', 'view_analytics'
    resource: str  # 'post', 'user', 'analytics'
    action: str  # 'create', 'read', 'update', 'delete'
```

### Permission System
```python
# src/domain/rbac.py
class PermissionChecker:
    def __init__(self, user_roles: List[Role]):
        self.user_roles = user_roles
    
    def can(self, permission: str, resource: str = None) -> bool:
        for role in self.user_roles:
            if permission in role.permissions:
                return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.user_roles)
```

---

## 6. Use Cases Layer

### Auth Use Cases with RBAC
```python
# src/use_cases/auth.py
class LoginUseCase:
    def __init__(self, user_repo, jwt_service):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
    
    def execute(self, email: str, password: str) -> AuthResult:
        user = self.user_repo.get_by_email(email)
        if not user or not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        
        user_roles = self.user_repo.get_user_roles(user.id)
        tokens = self.jwt_service.generate_tokens(
            user_id=user.id,
            roles=[role.name for role in user_roles]
        )
        return AuthResult(user=user, tokens=tokens)

class CheckPermissionUseCase:
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def execute(self, user_id: str, permission: str, resource: str = None) -> bool:
        user_roles = self.user_repo.get_user_roles(user_id)
        checker = PermissionChecker(user_roles)
        return checker.can(permission, resource)
```

---

## 7. Infrastructure Layer

### MongoDB Schema Design
```python
# Users collection
{
    "_id": "user_id",
    "email": "user@example.com",
    "password_hash": "bcrypt_hash",
    "roles": ["admin", "moderator"],
    "is_active": True,
    "is_verified": False,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T12:00:00Z"
}

# Roles collection
{
    "_id": "role_id",
    "name": "admin",
    "permissions": [
        "create_user",
        "delete_user", 
        "view_analytics",
        "manage_system"
    ],
    "description": "System administrator"
}

# Refresh tokens collection (for blacklisting)
{
    "_id": "token_id",
    "user_id": "user_id",
    "token_hash": "hashed_token",
    "expires_at": "2024-01-08T00:00:00Z",
    "is_revoked": False
}
```

---

## 8. Interface Layer

### Django Middleware
```python
# src/interfaces/rest/middleware.py
class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        user_id = self._extract_user_id(request)
        if user_id:
            user_roles = self._get_user_roles(user_id)
            request.user_roles = user_roles
            request.permission_checker = PermissionChecker(user_roles)
        
        response = self.get_response(request)
        return response

# Decorator for views
def require_permission(permission: str, resource: str = None):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'permission_checker'):
                raise AuthenticationError()
            
            if not request.permission_checker.can(permission, resource):
                raise PermissionDeniedError()
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### API Usage Examples
```python
# src/interfaces/rest/views.py
@require_permission('view_analytics')
def get_analytics(request):
    # Only users with 'view_analytics' permission can access
    pass

@require_permission('delete_user', resource='user')
def delete_user(request, user_id):
    # Only users who can delete users
    pass

# Role-based access
@admin_required  # Custom decorator
def system_settings(request):
    pass
```

---

## 9. Default Roles & Permissions

### Predefined Roles
```python
DEFAULT_ROLES = {
    'admin': [
        'create_user', 'delete_user', 'update_user',
        'create_post', 'delete_post', 'update_post',
        'view_analytics', 'manage_system'
    ],
    'moderator': [
        'create_post', 'delete_post', 'update_post',
        'view_analytics'
    ],
    'user': [
        'create_post', 'update_own_post', 'view_own_profile'
    ]
}
```

### JWT Enhancement
```python
# Include roles in JWT payload
jwt_payload = {
    'user_id': user.id,
    'email': user.email,
    'roles': [role.name for role in user_roles],
    'permissions': list(set().union(*[role.permissions for role in user_roles])),
    'exp': datetime.utcnow() + timedelta(minutes=15)
}
```

---

## 10. Dependencies to Add

```txt
djangorestframework>=3.14.0
PyJWT>=2.8.0
bcrypt>=4.0.0
redis>=4.5.0  # for token blacklisting
celery>=5.3.0  # for email sending
```

---

## 11. Environment Variables

```env
# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=900  # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis Configuration (for token blacklisting)
REDIS_URL=redis://localhost:6379/0
```

---

## 12. Implementation Strategy

### Phase 1: Core Authentication
- Basic auth with password hashing and JWT
- User registration and login
- Basic role assignment

### Phase 2: Security Enhancements
- Email verification
- Password reset flow
- Token blacklisting

### Phase 3: RBAC Implementation
- Permission system
- Role management
- Access control middleware

### Phase 4: Advanced Features
- Rate limiting
- Session management
- Device tracking
- Advanced security features

---

## 13. Advantages of This Approach

1. **Clean Architecture**: RBAC logic stays in domain layer
2. **Flexible**: Easy to add new roles/permissions
3. **Scalable**: Permission checking is O(1) after initial load
4. **Django-agnostic**: Can be reused with other frameworks
5. **Testable**: Easy to unit test permission logic
6. **Secure**: Follows security best practices
7. **Maintainable**: Clear separation of concerns

---

## 14. API Endpoints Design

### Authentication Endpoints
```
POST /api/auth/register     - User registration
POST /api/auth/login        - User login
POST /api/auth/refresh      - Refresh access token
POST /api/auth/logout       - Logout (blacklist token)
POST /api/auth/verify-email - Email verification
POST /api/auth/forgot-password - Password reset request
POST /api/auth/reset-password - Password reset confirmation
```

### User Management Endpoints
```
GET    /api/users/profile   - Get current user profile
PUT    /api/users/profile   - Update current user profile
GET    /api/users           - List users (admin only)
POST   /api/users           - Create user (admin only)
PUT    /api/users/{id}      - Update user (admin only)
DELETE /api/users/{id}      - Delete user (admin only)
```

### Role Management Endpoints
```
GET    /api/roles           - List roles (admin only)
POST   /api/roles           - Create role (admin only)
PUT    /api/roles/{id}      - Update role (admin only)
DELETE /api/roles/{id}      - Delete role (admin only)
POST   /api/users/{id}/roles - Assign role to user (admin only)
```

---

## 15. Error Handling

### Standardized Error Responses
```python
{
    "error": {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password",
        "details": {}
    }
}
```

### Common Error Codes
- `INVALID_CREDENTIALS` - Wrong email/password
- `PERMISSION_DENIED` - Insufficient permissions
- `TOKEN_EXPIRED` - JWT token has expired
- `TOKEN_INVALID` - JWT token is invalid
- `USER_NOT_FOUND` - User does not exist
- `EMAIL_ALREADY_EXISTS` - Email already registered
- `WEAK_PASSWORD` - Password does not meet requirements
