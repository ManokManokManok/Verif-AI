"""
MongoDB Connection Module

Manages MongoDB client lifecycle with optional TLS enforcement and role-based access.

Security:
    - TLS enforcement is configurable via MONGODB_REQUIRE_TLS env var
    - For production (Atlas / remote), set MONGODB_REQUIRE_TLS=true
    - For local development, TLS is not required by default
    - Connection is validated on first use with a ping
    - Supports role-based access control (backend, analytics, admin)

Role-Based Access:
    - backend: Full read/write access for application operations (default)
    - analytics: Read-only access for reporting and analytics
    - admin: Database administration access for migrations and maintenance
    
    Set environment variables:
    - MONGODB_URI (default/backend user)
    - MONGODB_URI_BACKEND (explicit backend user)
    - MONGODB_URI_ANALYTICS (read-only user)
    - MONGODB_URI_ADMIN (admin user)
"""

from pathlib import Path
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load env from project root
BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / '.env')

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')

_DEF_URI = os.getenv('MONGODB_URI')
_DEF_DB = os.getenv('MONGODB_DB_NAME', 'verfai')

# Store multiple clients (one per role) for least privilege access
_clients = {}


def _is_remote_uri(uri: str) -> bool:
    """Check if URI points to a remote MongoDB (Atlas, cloud, etc.)."""
    remote_indicators = ['mongodb+srv://', '.mongodb.net', '.mongodb.com']
    uri_lower = uri.lower()
    # Also consider non-localhost hosts as remote
    if 'mongodb://' in uri_lower:
        # Extract host part
        after_scheme = uri_lower.split('://', 1)[1]
        host_part = after_scheme.split('@')[-1].split('/')[0].split('?')[0]
        local_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
        host_name = host_part.split(':')[0]
        if host_name not in local_hosts:
            return True
    return any(indicator in uri_lower for indicator in remote_indicators)


def _enforce_tls(uri: str) -> str:
    """
    Ensure TLS parameters are present in a remote MongoDB URI.

    For remote/Atlas connections, appends tls=true and
    tlsAllowInvalidCertificates=false if not already set.

    Args:
        uri: MongoDB connection string

    Returns:
        URI with TLS parameters enforced
    """
    uri_lower = uri.lower()

    # Check if TLS is already configured
    if 'tls=true' in uri_lower or 'ssl=true' in uri_lower:
        # Ensure invalid certs are rejected
        if 'tlsallowinvalidcertificates=true' in uri_lower:
            security_logger.warning(
                '[SECURITY] tlsAllowInvalidCertificates=true detected. '
                'This is insecure for production.'
            )
        return uri

    # Add TLS parameters
    separator = '&' if '?' in uri else '?'
    enforced_uri = f"{uri}{separator}tls=true&tlsAllowInvalidCertificates=false"
    security_logger.info('[SECURITY] TLS enforced on MongoDB connection')
    return enforced_uri


def get_mongo_client(uri: str | None = None, role: str = 'backend') -> MongoClient:
    """
    Get or create a MongoDB client for a specific role.

    Supports role-based access control to implement least privilege principle:
    - backend: Full read/write access (default)
    - analytics: Read-only access for reporting
    - admin: Database administration access

    Security:
        - Enforces TLS for remote connections (Atlas, cloud)
        - Validates connectivity with a ping on first connect
        - Logs connection security status
        - Maintains separate client instances per role

    Args:
        uri: Optional MongoDB URI override (uses role-specific env var if None)
             If provided, bypasses role-based URI selection
        role: User role (backend/analytics/admin) - determines which URI to use
              Only used if uri parameter is None

    Returns:
        MongoClient instance for the specified role

    Raises:
        RuntimeError: If MongoDB URI is not set or connection fails
        ValueError: If invalid role is specified

    Examples:
        # Get default backend client
        client = get_mongo_client()
        
        # Get read-only client for analytics
        client = get_mongo_client(role='analytics')
        
        # Get admin client for migrations
        client = get_mongo_client(role='admin')
        
        # Override with custom URI (legacy compatibility)
        client = get_mongo_client(uri='mongodb://localhost:27017/')
    """
    global _clients
    
    # Validate role
    valid_roles = ['backend', 'analytics', 'admin']
    if role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")
    
    # Use provided URI or get role-specific URI from environment
    if uri is None:
        # Try role-specific URI first (e.g., MONGODB_URI_ANALYTICS)
        # Fall back to MONGODB_URI for backward compatibility
        role_uri_key = f'MONGODB_URI_{role.upper()}'
        uri = os.getenv(role_uri_key) or _DEF_URI
        
        if not uri:
            raise RuntimeError(
                f'{role_uri_key} or MONGODB_URI is not set. '
                f'Add it to .env for role-based access control.'
            )
        
        # Use role as cache key for multiple clients
        client_key = role
    else:
        # Custom URI provided - use URI as cache key for backward compatibility
        client_key = uri
    
    # Return existing client if already connected
    if client_key in _clients:
        return _clients[client_key]
    
    # Create new client connection
    require_tls = os.getenv('MONGODB_REQUIRE_TLS', '').lower() in ('1', 'true', 'yes')
    is_remote = _is_remote_uri(uri)

    # Enforce TLS for remote connections or when explicitly required
    if is_remote or require_tls:
        uri = _enforce_tls(uri)
        security_logger.info(
            '[SECURITY] MongoDB TLS enforced (role=%s, remote=%s, required=%s)',
            role, is_remote, require_tls
        )
    else:
        logger.info('MongoDB connecting locally (role=%s, TLS not required)', role)

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Validate connection
        client.admin.command('ping')
        logger.info('MongoDB connection established successfully (role=%s)', role)
        
        # Cache the client
        _clients[client_key] = client
        
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        security_logger.error('[SECURITY] MongoDB connection failed (role=%s): %s', role, e)
        raise RuntimeError(f'Failed to connect to MongoDB (role={role}): {e}')


def get_database(db_name: str | None = None):
    """Get a MongoDB database instance."""
    client = get_mongo_client()
    name = db_name or _DEF_DB
    if not name:
        raise RuntimeError('MONGODB_DB_NAME is not set. Add it to .env')
    return client[name]


def get_database_name() -> str:
    """Get database name from environment."""
    return os.getenv('MONGODB_DB_NAME', 'verfai')


def reset_client(role: str | None = None):
    """
    Reset the cached MongoDB client(s).
    Useful for testing or reconnection after errors.
    
    Args:
        role: Optional role to reset. If None, resets all clients.
    """
    global _clients
    
    if role is None:
        # Reset all clients
        for client in _clients.values():
            try:
                client.close()
            except Exception:
                pass
        _clients.clear()
        logger.info('All MongoDB clients reset')
    else:
        # Reset specific role client
        if role in _clients:
            try:
                _clients[role].close()
            except Exception:
                pass
            del _clients[role]
            logger.info('MongoDB client reset (role=%s)', role)
