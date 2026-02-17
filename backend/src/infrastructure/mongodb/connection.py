"""
MongoDB Connection Module

Manages MongoDB client lifecycle with optional TLS enforcement.

Security:
    - TLS enforcement is configurable via MONGODB_REQUIRE_TLS env var
    - For production (Atlas / remote), set MONGODB_REQUIRE_TLS=true
    - For local development, TLS is not required by default
    - Connection is validated on first use with a ping
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

_client = None


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


def get_mongo_client(uri: str | None = None) -> MongoClient:
    """
    Get or create the singleton MongoDB client.

    Security:
        - Enforces TLS for remote connections (Atlas, cloud)
        - Validates connectivity with a ping on first connect
        - Logs connection security status

    Args:
        uri: Optional MongoDB URI override (uses MONGODB_URI env var if None)

    Returns:
        MongoClient instance

    Raises:
        RuntimeError: If MONGODB_URI is not set or connection fails
    """
    global _client
    if _client is None:
        uri = uri or _DEF_URI
        if not uri:
            raise RuntimeError('MONGODB_URI is not set. Add it to .env')

        require_tls = os.getenv('MONGODB_REQUIRE_TLS', '').lower() in ('1', 'true', 'yes')
        is_remote = _is_remote_uri(uri)

        # Enforce TLS for remote connections or when explicitly required
        if is_remote or require_tls:
            uri = _enforce_tls(uri)
            security_logger.info(
                '[SECURITY] MongoDB TLS enforced (remote=%s, required=%s)',
                is_remote, require_tls
            )
        else:
            logger.info('MongoDB connecting locally (TLS not required)')

        try:
            _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Validate connection
            _client.admin.command('ping')
            logger.info('MongoDB connection established successfully')
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            _client = None
            security_logger.error('[SECURITY] MongoDB connection failed: %s', e)
            raise RuntimeError(f'Failed to connect to MongoDB: {e}')

    return _client


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


def reset_client():
    """
    Reset the cached MongoDB client.
    Useful for testing or reconnection after errors.
    """
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
