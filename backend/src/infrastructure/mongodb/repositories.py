from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from datetime import datetime, timezone
from bson import ObjectId

from ...domain.entities import User, Role, Permission, UserAlreadyExistsError, UserNotFoundError


def _now_utc_naive() -> datetime:
    return datetime.utcnow()


def _to_utc_naive(value: datetime) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


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
                "created_at": _now_utc_naive(),
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
                "created_at": _now_utc_naive(),
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
                "expires_at": {"$gt": _now_utc_naive()}
            })
            
            if not token_doc:
                return None
            
            # Mark token as used
            self.verification_tokens_collection.update_one(
                {"_id": token_doc["_id"]},
                {"$set": {"is_used": True, "used_at": _now_utc_naive()}}
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
                "expires_at": {"$gt": _now_utc_naive()}
            })
            
            if not token_doc:
                return None
            
            # Mark token as used
            self.password_reset_tokens_collection.update_one(
                {"_id": token_doc["_id"]},
                {"$set": {"is_used": True, "used_at": _now_utc_naive()}}
            )
            
            return token_doc["user_id"]
        except Exception:
            return None

    def get_password_reset_token_status(self, token: str) -> Dict[str, Optional[str]]:
        """
        Get password reset token status without consuming the token.

        Returns:
            {
                "status": "valid" | "expired" | "used" | "invalid",
                "user_id": Optional[str]
            }
        """
        try:
            token_doc = self.password_reset_tokens_collection.find_one({"token": token})
            if not token_doc:
                return {"status": "invalid", "user_id": None}

            user_id = token_doc.get("user_id")
            if token_doc.get("is_used"):
                return {"status": "used", "user_id": user_id}

            expires_at = _to_utc_naive(token_doc.get("expires_at"))
            if expires_at and expires_at <= _now_utc_naive():
                return {"status": "expired", "user_id": user_id}

            return {"status": "valid", "user_id": user_id}
        except Exception:
            return {"status": "invalid", "user_id": None}

    def invalidate_password_reset_token(self, token: str) -> bool:
        """
        Invalidate password reset token so it cannot be reused.

        Returns:
            True if token document was updated, False otherwise.
        """
        try:
            result = self.password_reset_tokens_collection.update_one(
                {"token": token, "is_used": False},
                {"$set": {"is_used": True, "used_at": _now_utc_naive()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
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
                {"$set": {"is_verified": True, "verified_at": _now_utc_naive()}}
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
                {"$set": {"password_hash": password_hash, "password_updated_at": _now_utc_naive()}}
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
                "expires_at": {"$lt": _now_utc_naive()}
            })
            
            # Clean expired password reset tokens
            reset_result = self.password_reset_tokens_collection.delete_many({
                "expires_at": {"$lt": _now_utc_naive()}
            })
            
            return verification_result.deleted_count + reset_result.deleted_count
        except Exception:
            return 0


class MongoDBUserRepository:
    def __init__(self, client: MongoClient, database_name: str):
        self.db: Database = client[database_name]
        self.users_collection: Collection = self.db.users
        self.archived_users_collection: Collection = self.db.archived_users
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
        # Add user_id field (string of _id) for easier tracking
        self.users_collection.update_one({"_id": result.inserted_id}, {"$set": {"user_id": user.id}})
        user_dict["user_id"] = user.id
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
        from datetime import timezone
        try:
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            if result.matched_count == 0:
                import logging
                logging.getLogger(__name__).warning(
                    f"update_last_login: no document matched for user_id={user_id}"
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"update_last_login failed for user_id={user_id}: {e}"
            )
    
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
    
    # ==================== Admin User Management Methods ====================
    
    def get_all_users(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for descending, 1 for ascending
    ) -> tuple:
        """
        Get all users with filtering and pagination (Admin only).
        
        Args:
            search: Search term for email or username
            role: Filter by role name
            is_active: Filter by active status
            is_verified: Filter by verification status
            limit: Maximum results to return
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_order: Sort direction (-1 desc, 1 asc)
        
        Returns:
            Tuple of (list of User entities, total count)
        """
        filter_query = {
            # Exclude soft-deleted users by default
            "$or": [
                {"deleted": {"$exists": False}},
                {"deleted": False}
            ]
        }
        
        # Search filter (email or username)
        if search:
            # Need to combine with existing $or using $and
            filter_query = {
                "$and": [
                    filter_query,
                    {
                        "$or": [
                            {"email": {"$regex": search, "$options": "i"}},
                            {"username": {"$regex": search, "$options": "i"}}
                        ]
                    }
                ]
            }
        
        # Role filter
        if role:
            if "$and" in filter_query:
                filter_query["$and"].append({"roles": role})
            else:
                filter_query["roles"] = role
        
        # Status filters
        if is_active is not None:
            if "$and" in filter_query:
                filter_query["$and"].append({"is_active": is_active})
            else:
                filter_query["is_active"] = is_active
        if is_verified is not None:
            if "$and" in filter_query:
                filter_query["$and"].append({"is_verified": is_verified})
            else:
                filter_query["is_verified"] = is_verified
        
        # Get total count
        total_count = self.users_collection.count_documents(filter_query)
        
        # Get paginated results
        cursor = self.users_collection.find(filter_query)\
            .sort(sort_by, sort_order)\
            .skip(offset)\
            .limit(limit)
        
        users = [self._document_to_user(doc) for doc in cursor]
        
        return users, total_count
    
    def delete_user(self, user_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a user account (Admin only).
        
        Args:
            user_id: User's ID to delete
            hard_delete: If True, permanently remove; if False, soft delete (deactivate)
        
        Returns:
            True if user was deleted successfully
        
        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                raise UserNotFoundError(f"User {user_id} not found")
            
            if hard_delete:
                # Permanently delete user
                result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
                return result.deleted_count > 0
            else:
                # Archive the user: move document to archived_users collection
                archive_doc = dict(user_doc)
                archive_doc["archived_at"] = datetime.utcnow()
                archive_doc["archive_reason"] = "admin_soft_delete"
                archive_doc["original_id"] = str(user_doc["_id"])
                # Store with a fresh _id so archived_users can hold multiple versions
                del archive_doc["_id"]
                self.archived_users_collection.insert_one(archive_doc)
                # Remove from active users collection
                result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
                return result.deleted_count > 0
        except UserNotFoundError:
            raise
        except Exception as e:
            return False
    
    def admin_reset_password(self, user_id: str, new_password_hash: str) -> bool:
        """
        Admin-initiated password reset for a user.
        
        Args:
            user_id: User's ID
            new_password_hash: New hashed password
        
        Returns:
            True if password was updated successfully
        
        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                raise UserNotFoundError(f"User {user_id} not found")
            
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "password_updated_at": datetime.utcnow(),
                        "password_reset_by_admin": True,
                        "force_password_change": True  # Optional: force user to change on next login
                    }
                }
            )
            return result.modified_count > 0
        except UserNotFoundError:
            raise
        except Exception:
            return False
    
    def update_user_status(self, user_id: str, is_active: bool = None, status: str = None) -> bool:
        """
        Update a user account status (Admin only).
        
        Supports both the new `status` string field ('active', 'inactive', 'suspended')
        and the legacy `is_active` boolean for backward compatibility.
        
        Args:
            user_id: User's ID
            is_active: Legacy boolean active status (deprecated, use status)
            status: New status string ('active', 'inactive', 'suspended')
        
        Returns:
            True if status was updated successfully
        
        Raises:
            UserNotFoundError: If user not found
            ValueError: If neither status nor is_active is provided, or invalid status
        """
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                raise UserNotFoundError(f"User {user_id} not found")
            
            update_data = {
                "status_updated_at": datetime.utcnow()
            }
            
            # Handle new status string field
            if status is not None:
                valid_statuses = ["active", "inactive", "suspended"]
                if status not in valid_statuses:
                    raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
                update_data["status"] = status
                update_data["is_active"] = (status == "active")
            # Handle legacy is_active boolean
            elif is_active is not None:
                update_data["is_active"] = is_active
                update_data["status"] = "active" if is_active else "inactive"
            else:
                raise ValueError("Either status or is_active must be provided")
            
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except (UserNotFoundError, ValueError):
            raise
        except Exception:
            return False
    
    def update_user_roles(self, user_id: str, roles: List[str]) -> bool:
        """
        Update a user's roles (Admin only).
        
        Args:
            user_id: User's ID
            roles: New list of role names
        
        Returns:
            True if roles were updated successfully
        
        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                raise UserNotFoundError(f"User {user_id} not found")
            
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "roles": roles,
                        "roles_updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except UserNotFoundError:
            raise
        except Exception:
            return False
    
    def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get activity summary for a user (Admin only).
        """
        from .analysis_repository import AnalysisResultRepository
        
        try:
            user = self.get_by_id(user_id)
            if not user:
                return {}
            
            # Get analysis count for this user
            analysis_count = self.db.analysis_results.count_documents({"user_id": user_id})
            
            # Get last analysis date
            last_analysis = self.db.analysis_results.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            last_analysis_date = last_analysis.get("created_at") if last_analysis else None
            
            return {
                "user_id": user_id,
                "email": user.email,
                "username": user.username,
                "total_analyses": analysis_count,
                "last_analysis_at": last_analysis_date,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "roles": user.roles,
            }
        except Exception:
            return {}
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username (case-insensitive)."""
        user_doc = self.users_collection.find_one(
            {"username": {"$regex": f"^{username}$", "$options": "i"}}
        )
        if not user_doc:
            return None
        return self._document_to_user(user_doc)
    
    def update_username(self, user_id: str, new_username: str) -> bool:
        """Update a user's username."""
        try:
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"username": new_username, "username_updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def self_delete_user(self, user_id: str) -> bool:
        """
        Self-service account deletion. Archives the user then removes from active collection.
        """
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                raise UserNotFoundError(f"User {user_id} not found")
            
            archive_doc = dict(user_doc)
            archive_doc["archived_at"] = datetime.utcnow()
            archive_doc["archive_reason"] = "self_delete"
            archive_doc["original_id"] = str(user_doc["_id"])
            del archive_doc["_id"]
            self.archived_users_collection.insert_one(archive_doc)
            
            result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except UserNotFoundError:
            raise
        except Exception:
            return False
    
    def _document_to_user(self, doc: Dict[str, Any]) -> User:
        """Convert MongoDB document to User entity."""
        # Derive status from stored value or fall back to is_active boolean
        is_active = doc.get("is_active", True)
        stored_status = doc.get("status")
        if stored_status and stored_status in ("active", "inactive", "suspended"):
            status = stored_status
        else:
            status = "active" if is_active else "inactive"
        
        return User(
            id=str(doc["_id"]),
            email=doc["email"],
            username=doc.get("username"),
            password_hash=doc["password_hash"],
            roles=doc.get("roles", []),
            is_active=is_active,
            is_verified=doc.get("is_verified", False),
            status=status,
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
