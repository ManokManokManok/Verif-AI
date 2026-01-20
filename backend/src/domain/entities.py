from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class User:
    id: Optional[str]
    email: str
    username: Optional[str]
    password_hash: str
    roles: List[str]
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Role:
    id: Optional[str]
    name: str
    permissions: List[str]
    description: str = ""


@dataclass
class Permission:
    id: Optional[str]
    name: str
    resource: str
    action: str
    description: str = ""


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class AuthResult:
    user: User
    tokens: AuthTokens


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


class AuthenticationError(Exception):
    pass
