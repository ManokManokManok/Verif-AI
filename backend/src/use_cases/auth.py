from typing import Protocol, List
from ..domain.entities import User, AuthResult, UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError
from ..domain.services import PasswordHasher, EmailValidator, PasswordValidator
from ..infrastructure.jwt_service import JWTService
from ..infrastructure.mongodb.repositories import MongoDBUserRepository


class UserRepository(Protocol):
    def create_user(self, user: User) -> User: ...
    def get_by_email(self, email: str) -> User: ...
    def get_by_id(self, user_id: str) -> User: ...
    def update_last_login(self, user_id: str) -> None: ...
    def get_user_roles(self, user_id: str) -> List: ...


class SignupUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        email_validator: EmailValidator,
        password_validator: PasswordValidator
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.email_validator = email_validator
        self.password_validator = password_validator
    
    def execute(self, email: str, password: str, username: str = None) -> User:
        """
        Register a new user.
        
        Args:
            email: User's email
            password: Plain text password
            username: User's username (optional)
        
        Returns:
            Created user entity
        
        Raises:
            UserAlreadyExistsError: If user with email already exists
            ValueError: If email or password is invalid
        """
        # Validate email
        is_valid_email, email_error = self.email_validator.validate(email)
        if not is_valid_email:
            raise ValueError(email_error)
        
        # Validate password
        is_valid_password, password_errors = self.password_validator.validate(password)
        if not is_valid_password:
            raise ValueError("Password validation failed: " + "; ".join(password_errors))
        
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email {email} already exists")
        
        # Hash password
        password_hash = self.password_hasher.hash_password(password)
        
        # Create user with default role
        user = User(
            id=None,
            email=email,
            password_hash=password_hash,
            roles=["user"],  # Default role
            username=username,
            is_active=True,
            is_verified=False  # Will be verified in Phase 2
        )
        
        # Save user
        created_user = self.user_repository.create_user(user)
        
        return created_user


class LoginUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        jwt_service: JWTService
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.jwt_service = jwt_service
    
    def execute(self, email: str, password: str) -> AuthResult:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User's email
            password: Plain text password
        
        Returns:
            AuthResult containing user and tokens
        
        Raises:
            InvalidCredentialsError: If email or password is invalid
        """
        # Get user by email
        user = self.user_repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise InvalidCredentialsError("Account is deactivated")
        
        # Verify password
        if not self.password_hasher.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # Get user roles and permissions
        user_roles = self.user_repository.get_user_roles(user.id)
        role_names = [role.name for role in user_roles]
        permissions = []
        for role in user_roles:
            permissions.extend(role.permissions)
        
        # Generate tokens
        tokens = self.jwt_service.generate_tokens(
            user_id=user.id,
            email=user.email,
            roles=role_names,
            permissions=list(set(permissions))  # Remove duplicates
        )
        
        # Update last login
        self.user_repository.update_last_login(user.id)
        
        return AuthResult(user=user, tokens=tokens)


class CheckPermissionUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def execute(self, user_id: str, permission: str, resource: str = None) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: User's ID
            permission: Permission to check
            resource: Optional resource to check
        
        Returns:
            True if user has permission, False otherwise
        """
        try:
            user_roles = self.user_repository.get_user_roles(user_id)
            for role in user_roles:
                if permission in role.permissions:
                    return True
            return False
        except:
            return False


class GetUserProfileUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def execute(self, user_id: str) -> User:
        """
        Get user profile by ID.
        
        Args:
            user_id: User's ID
        
        Returns:
            User entity
        
        Raises:
            UserNotFoundError: If user is not found
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return user
