from typing import Protocol
from datetime import datetime, timedelta


class TokenBlacklistService(Protocol):
    def blacklist_token(self, token: str, expires_at: datetime) -> bool:
        ...
    
    def is_token_blacklisted(self, token: str) -> bool:
        ...
    
    def cleanup_expired_tokens(self) -> int:
        ...


class MongoDBTokenBlacklistService:
    """
    MongoDB-based token blacklisting service.
    Stores blacklisted tokens in a MongoDB collection.
    """
    
    def __init__(self, client, database_name: str):
        self.db = client[database_name]
        self.blacklisted_tokens_collection = self.db.blacklisted_tokens
    
    def blacklist_token(self, token: str, expires_at: datetime) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: JWT token to blacklist
            expires_at: Token expiration time
        
        Returns:
            True if token was successfully blacklisted
        """
        try:
            # Check if token is already blacklisted
            existing = self.blacklisted_tokens_collection.find_one({"token": token})
            if existing:
                return True
            
            # Add token to blacklist
            self.blacklisted_tokens_collection.insert_one({
                "token": token,
                "blacklisted_at": datetime.utcnow(),
                "expires_at": expires_at
            })
            
            return True
        except Exception:
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: JWT token to check
        
        Returns:
            True if token is blacklisted, False otherwise
        """
        try:
            blacklisted = self.blacklisted_tokens_collection.find_one({"token": token})
            if not blacklisted:
                return False
            
            # Check if token has expired (should be cleaned up)
            if blacklisted["expires_at"] < datetime.utcnow():
                # Remove expired token
                self.blacklisted_tokens_collection.delete_one({"_id": blacklisted["_id"]})
                return False
            
            return True
        except Exception:
            return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from blacklist.
        
        Returns:
            Number of tokens removed
        """
        try:
            result = self.blacklisted_tokens_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            return result.deleted_count
        except Exception:
            return 0


class MockTokenBlacklistService:
    """
    Mock token blacklisting service for development/testing.
    Uses an in-memory set to store blacklisted tokens.
    """
    
    def __init__(self):
        self.blacklisted_tokens = set()
        self.token_expirations = {}
    
    def blacklist_token(self, token: str, expires_at: datetime) -> bool:
        """
        Add a token to the blacklist (mock implementation).
        
        Args:
            token: JWT token to blacklist
            expires_at: Token expiration time
        
        Returns:
            True if token was successfully blacklisted
        """
        self.blacklisted_tokens.add(token)
        self.token_expirations[token] = expires_at
        print(f"MOCK: Blacklisted token: {token[:20]}...")
        return True
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted (mock implementation).
        
        Args:
            token: JWT token to check
        
        Returns:
            True if token is blacklisted, False otherwise
        """
        if token not in self.blacklisted_tokens:
            return False
        
        # Check if token has expired
        expires_at = self.token_expirations.get(token)
        if expires_at and expires_at < datetime.utcnow():
            self.blacklisted_tokens.remove(token)
            del self.token_expirations[token]
            return False
        
        return True
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from blacklist (mock implementation).
        
        Returns:
            Number of tokens removed
        """
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, expires_at in self.token_expirations.items():
            if expires_at < current_time:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            self.blacklisted_tokens.discard(token)
            del self.token_expirations[token]
        
        print(f"MOCK: Cleaned up {len(expired_tokens)} expired tokens")
        return len(expired_tokens)
