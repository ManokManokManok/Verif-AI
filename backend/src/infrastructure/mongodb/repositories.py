from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from datetime import datetime
from bson import ObjectId

from ...domain.entities import User, Role, Permission, UserAlreadyExistsError, UserNotFoundError


class MongoDBTokenRepository:
    """
    MongoDB repository for handling verification and password reset tokens.
    """
    
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.users_collection: Collection = self.db.users
        self.verification_tokens_collection: Collection = self.db.verification_tokens
        self.password_reset_tokens_collection: Collection = self.db.password_reset_tokens
    
    def create_verification_token(self, user_id: str, token: str, expires_at: datetime) -> bool:
        """
        Create email verification token.
        
        Args:
            user_id: User's ID
            token: Verification token
            expires_at: Token expiration time
        
        Returns:
            True if token was created successfully
        """
        try:
            # Delete any existing verification tokens for this user
            self.verification_tokens_collection.delete_many({"user_id": user_id})
            
            # Create new token
            self.verification_tokens_collection.insert_one({
                "user_id": user_id,
                "token": token,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_used": False
            })
            return True
        except Exception:
            return False
    
    def create_password_reset_token(self, user_id: str, token: str, expires_at: datetime) -> bool:
        """
        Create password reset token.
        
        Args:
            user_id: User's ID
            token: Reset token
            expires_at: Token expiration time
        
        Returns:
            True if token was created successfully
        """
        try:
            # Delete any existing reset tokens for this user
            self.password_reset_tokens_collection.delete_many({"user_id": user_id})
            
            # Create new token
            self.password_reset_tokens_collection.insert_one({
                "user_id": user_id,
                "token": token,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_used": False
            })
            return True
        except Exception:
            return False
    
    def verify_email_token(self, token: str) -> Optional[str]:
        """
        Verify email verification token and return user ID.
        
        Args:
            token: Verification token
        
        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            token_doc = self.verification_tokens_collection.find_one({
                "token": token,
                "is_used": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not token_doc:
                return None
            
            # Mark token as used
            self.verification_tokens_collection.update_one(
                {"_id": token_doc["_id"]},
                {"$set": {"is_used": True, "used_at": datetime.utcnow()}}
            )
            
            return token_doc["user_id"]
        except Exception:
            return None
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """
        Verify password reset token and return user ID.
        
        Args:
            token: Reset token
        
        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            token_doc = self.password_reset_tokens_collection.find_one({
                "token": token,
                "is_used": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not token_doc:
                return None
            
            # Mark token as used
            self.password_reset_tokens_collection.update_one(
                {"_id": token_doc["_id"]},
                {"$set": {"is_used": True, "used_at": datetime.utcnow()}}
            )
            
            return token_doc["user_id"]
        except Exception:
            return None
    
    def update_user_verification(self, user_id: str) -> bool:
        """
        Mark user as verified.
        
        Args:
            user_id: User's ID
        
        Returns:
            True if user was updated successfully
        """
        try:
            self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_verified": True, "verified_at": datetime.utcnow()}}
            )
            return True
        except Exception:
            return False
    
    def update_user_password(self, user_id: str, password_hash: str) -> bool:
        """
        Update user's password.
        
        Args:
            user_id: User's ID
            password_hash: New password hash
        
        Returns:
            True if password was updated successfully
        """
        try:
            self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password_hash": password_hash, "password_updated_at": datetime.utcnow()}}
            )
            return True
        except Exception:
            return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from database.
        
        Returns:
            Number of tokens removed
        """
        try:
            # Clean expired verification tokens
            verification_result = self.verification_tokens_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            # Clean expired password reset tokens
            reset_result = self.password_reset_tokens_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            return verification_result.deleted_count + reset_result.deleted_count
        except Exception:
            return 0


class MongoDBUserRepository:
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.users_collection: Collection = self.db.users
        self.roles_collection: Collection = self.db.roles
    
    def create_user(self, user: User) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User entity to create
        
        Returns:
            Created user with generated ID
        
        Raises:
            UserAlreadyExistsError: If user with email already exists
        """
        # Check if user already exists
        existing_user = self.users_collection.find_one({"email": user.email})
        if existing_user:
            raise UserAlreadyExistsError(f"User with email {user.email} already exists")
        
        # Convert user to dict
        user_dict = {
            "email": user.email,
            "username": user.username,
            "password_hash": user.password_hash,
            "roles": user.roles,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at or datetime.utcnow(),
            "last_login": user.last_login
        }
        
        # Insert user
        result = self.users_collection.insert_one(user_dict)
        user.id = str(result.inserted_id)
        
        return user
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User's email
        
        Returns:
            User entity if found, None otherwise
        """
        user_doc = self.users_collection.find_one({"email": email})
        if not user_doc:
            return None
        
        return self._document_to_user(user_doc)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User's ID
        
        Returns:
            User entity if found, None otherwise
        """
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
        except:
            return None
        
        if not user_doc:
            return None
        
        return self._document_to_user(user_doc)
    
    def update_last_login(self, user_id: str) -> None:
        """
        Update user's last login time.
        
        Args:
            user_id: User's ID
        """
        try:
            self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except:
            pass
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """
        Get all roles for a user.
        
        Args:
            user_id: User's ID
        
        Returns:
            List of Role entities
        """
        try:
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        except:
            return []
        
        if not user or not user.get("roles"):
            return []
        
        # Get role documents
        role_docs = self.roles_collection.find({"name": {"$in": user["roles"]}})
        return [self._document_to_role(role_doc) for role_doc in role_docs]
    
    def _document_to_user(self, doc: Dict[str, Any]) -> User:
        """Convert MongoDB document to User entity."""
        return User(
            id=str(doc["_id"]),
            email=doc["email"],
            username=doc.get("username"),
            password_hash=doc["password_hash"],
            roles=doc.get("roles", []),
            is_active=doc.get("is_active", True),
            is_verified=doc.get("is_verified", False),
            created_at=doc.get("created_at"),
            last_login=doc.get("last_login")
        )
    
    def _document_to_role(self, doc: Dict[str, Any]) -> Role:
        """Convert MongoDB document to Role entity."""
        return Role(
            id=str(doc["_id"]),
            name=doc["name"],
            permissions=doc.get("permissions", []),
            description=doc.get("description", "")
        )


class MongoDBRoleRepository:
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.roles_collection: Collection = self.db.roles
    
    def create_role(self, role: Role) -> Role:
        """
        Create a new role in the database.
        
        Args:
            role: Role entity to create
        
        Returns:
            Created role with generated ID
        """
        role_dict = {
            "name": role.name,
            "permissions": role.permissions,
            "description": role.description
        }
        
        result = self.roles_collection.insert_one(role_dict)
        role.id = str(result.inserted_id)
        
        return role
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            name: Role name
        
        Returns:
            Role entity if found, None otherwise
        """
        role_doc = self.roles_collection.find_one({"name": name})
        if not role_doc:
            return None
        
        return self._document_to_role(role_doc)
    
    def get_all(self) -> List[Role]:
        """
        Get all roles.
        
        Returns:
            List of all Role entities
        """
        role_docs = self.roles_collection.find()
        return [self._document_to_role(doc) for doc in role_docs]
    
    def _document_to_role(self, doc: Dict[str, Any]) -> Role:
        """Convert MongoDB document to Role entity."""
        return Role(
            id=str(doc["_id"]),
            name=doc["name"],
            permissions=doc.get("permissions", []),
            description=doc.get("description", "")
        )
