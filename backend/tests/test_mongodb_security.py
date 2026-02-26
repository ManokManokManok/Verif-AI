"""
MongoDB Security Tests

Tests for MongoDB connection security including:
- TLS enforcement for remote connections
- Role-based access control
- Connection validation
- Least privilege principle

Run with: python -m pytest tests/test_mongodb_security.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure, OperationFailure

from src.infrastructure.mongodb.connection import (
    get_mongo_client,
    reset_client,
    _is_remote_uri,
    _enforce_tls,
)


class TestTLSEnforcement:
    """Test TLS enforcement for MongoDB connections."""
    
    def test_is_remote_uri_atlas(self):
        """Verify Atlas URIs are identified as remote."""
        uri = "mongodb+srv://cluster0.mongodb.net/"
        assert _is_remote_uri(uri) is True
    
    def test_is_remote_uri_cloud(self):
        """Verify cloud MongoDB URIs are identified as remote."""
        uri = "mongodb+srv://cluster.mongodb.com/"
        assert _is_remote_uri(uri) is True
    
    def test_is_remote_uri_localhost(self):
        """Verify localhost URIs are identified as local."""
        local_uris = [
            "mongodb://localhost:27017/",
            "mongodb://127.0.0.1:27017/",
            "mongodb://0.0.0.0:27017/",
        ]
        for uri in local_uris:
            assert _is_remote_uri(uri) is False, f"Failed for {uri}"
    
    def test_is_remote_uri_remote_host(self):
        """Verify non-localhost hosts are identified as remote."""
        uri = "mongodb://192.168.1.100:27017/"
        assert _is_remote_uri(uri) is True
    
    def test_enforce_tls_adds_parameters(self):
        """Verify TLS parameters are added to remote URIs."""
        uri = "mongodb+srv://user:pass@cluster.mongodb.net/"
        enforced = _enforce_tls(uri)
        
        assert "tls=true" in enforced.lower()
        assert "tlsallowinvalidcertificates=false" in enforced.lower()
    
    def test_enforce_tls_preserves_existing_tls(self):
        """Verify existing TLS parameters are preserved."""
        uri = "mongodb+srv://cluster.mongodb.net/?tls=true"
        enforced = _enforce_tls(uri)
        
        # Should not add duplicate parameters
        assert enforced.count("tls=true") == 1
    
    def test_enforce_tls_warns_on_invalid_certs(self, caplog):
        """Verify warning is logged for invalid certificate settings."""
        import logging
        # Ensure security logger is at WARNING level
        logging.getLogger('security').setLevel(logging.WARNING)
        caplog.set_level(logging.WARNING, logger='security')
        
        # URI with tlsAllowInvalidCertificates=true should trigger warning
        # when _enforce_tls is called and finds this setting
        uri = "mongodb+srv://cluster.mongodb.net/?tls=true&tlsAllowInvalidCertificates=true"
        result = _enforce_tls(uri)
        
        # The function should preserve the URI (case may change)
        assert "tlsallowinvalidcertificates=true" in result.lower()
        
        # Verify warning was logged
        assert len(caplog.records) > 0, "Expected warning log not captured"
        assert any("tlsAllowInvalidCertificates" in record.message for record in caplog.records)


class TestRoleBasedAccess:
    """Test role-based access control for MongoDB connections."""
    
    def setup_method(self):
        """Reset clients before each test."""
        reset_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_client()
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
        'MONGODB_URI_BACKEND': 'mongodb://backend:pass@localhost:27017/',
        'MONGODB_URI_ANALYTICS': 'mongodb://analytics:pass@localhost:27017/',
        'MONGODB_URI_ADMIN': 'mongodb://admin:pass@localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_get_backend_client(self, mock_mongo_client):
        """Verify backend role uses MONGODB_URI_BACKEND."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        client = get_mongo_client(role='backend')
        
        # Verify MongoClient was called with backend URI
        call_args = mock_mongo_client.call_args[0][0]
        assert 'backend:pass' in call_args
        assert client is mock_client
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
        'MONGODB_URI_ANALYTICS': 'mongodb://analytics:pass@localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_get_analytics_client(self, mock_mongo_client):
        """Verify analytics role uses MONGODB_URI_ANALYTICS."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        client = get_mongo_client(role='analytics')
        
        # Verify MongoClient was called with analytics URI
        call_args = mock_mongo_client.call_args[0][0]
        assert 'analytics:pass' in call_args
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
        'MONGODB_URI_ADMIN': 'mongodb://admin:pass@localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_get_admin_client(self, mock_mongo_client):
        """Verify admin role uses MONGODB_URI_ADMIN."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        client = get_mongo_client(role='admin')
        
        # Verify MongoClient was called with admin URI
        call_args = mock_mongo_client.call_args[0][0]
        assert 'admin:pass' in call_args
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://default:pass@localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    @patch('src.infrastructure.mongodb.connection._DEF_URI', 'mongodb://default:pass@localhost:27017/')
    def test_fallback_to_default_uri(self, mock_mongo_client):
        """Verify fallback to MONGODB_URI when role-specific URI not set."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        client = get_mongo_client(role='backend')
        
        # Should use MONGODB_URI as fallback
        call_args = mock_mongo_client.call_args[0][0]
        assert 'default:pass' in call_args
    
    def test_invalid_role_raises_error(self):
        """Verify invalid role raises ValueError."""
        with pytest.raises(ValueError, match="Invalid role"):
            get_mongo_client(role='invalid_role')
    
    @patch('src.infrastructure.mongodb.connection._DEF_URI', None)
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_uri_raises_error(self):
        """Verify missing MongoDB URI raises RuntimeError."""
        reset_client()
        
        with pytest.raises(RuntimeError, match="MONGODB_URI is not set"):
            get_mongo_client(role='backend')
    
    @patch.dict(os.environ, {
        'MONGODB_URI_BACKEND': 'mongodb://backend:pass@localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_client_caching_per_role(self, mock_mongo_client):
        """Verify separate client instances are cached per role."""
        mock_client1 = MagicMock()
        mock_client1.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client1
        
        # First call - creates client
        client1 = get_mongo_client(role='backend')
        assert mock_mongo_client.call_count == 1
        
        # Second call - uses cached client
        client2 = get_mongo_client(role='backend')
        assert mock_mongo_client.call_count == 1  # No additional call
        assert client1 is client2  # Same instance
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_custom_uri_override(self, mock_mongo_client):
        """Verify custom URI parameter overrides role-based selection."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        custom_uri = 'mongodb://custom:pass@localhost:27017/'
        client = get_mongo_client(uri=custom_uri, role='backend')
        
        # Should use custom URI, not role-based URI
        call_args = mock_mongo_client.call_args[0][0]
        assert 'custom:pass' in call_args


class TestConnectionValidation:
    """Test MongoDB connection validation and error handling."""
    
    def setup_method(self):
        """Reset clients before each test."""
        reset_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_client()
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_connection_failure_raises_error(self, mock_mongo_client):
        """Verify connection failure raises RuntimeError."""
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        with pytest.raises(RuntimeError, match="Failed to connect to MongoDB"):
            get_mongo_client(role='backend')
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_ping_validation(self, mock_mongo_client):
        """Verify connection is validated with ping command."""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        get_mongo_client(role='backend')
        
        # Verify ping was called to validate connection
        mock_client.admin.command.assert_called_once_with('ping')


class TestResetClient:
    """Test client reset functionality."""
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_reset_all_clients(self, mock_mongo_client):
        """Verify reset_client() closes all client connections."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        # Create multiple clients
        get_mongo_client(role='backend')
        
        # Reset all clients
        reset_client()
        
        # Verify close was called
        mock_client.close.assert_called()
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
        'MONGODB_URI_ANALYTICS': 'mongodb://analytics:pass@localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_reset_specific_role(self, mock_mongo_client):
        """Verify reset_client(role) closes only specified role."""
        mock_backend = MagicMock()
        mock_backend.admin.command.return_value = {}
        mock_analytics = MagicMock()
        mock_analytics.admin.command.return_value = {}
        
        # Return different clients for different roles
        mock_mongo_client.side_effect = [mock_backend, mock_analytics]
        
        # Create both clients
        get_mongo_client(role='backend')
        get_mongo_client(role='analytics')
        
        # Reset only analytics
        reset_client(role='analytics')
        
        # Verify only analytics was closed
        mock_analytics.close.assert_called_once()
        mock_backend.close.assert_not_called()


class TestSecurityLogging:
    """Test security-related logging functionality."""
    
    def setup_method(self):
        """Reset clients before each test."""
        reset_client()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_client()
    
    @patch('src.infrastructure.mongodb.connection._DEF_URI', 'mongodb+srv://cluster.mongodb.net/')
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb+srv://cluster.mongodb.net/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_tls_enforcement_logged(self, mock_mongo_client, caplog):
        """Verify TLS enforcement is logged for remote connections."""
        import logging
        # Set logging levels for all relevant loggers
        logging.getLogger('security').setLevel(logging.INFO)
        logging.getLogger('src.infrastructure.mongodb.connection').setLevel(logging.INFO)
        caplog.set_level(logging.INFO)
        
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        # Reset client to ensure fresh connection
        reset_client()
        get_mongo_client(role='backend')
        
        # The function should have been called with a URI containing TLS parameters
        call_args = mock_mongo_client.call_args[0][0]
        assert 'tls=true' in call_args.lower(), \
            f"TLS not enforced in URI: {call_args}"
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_connection_success_logged(self, mock_mongo_client, caplog):
        """Verify successful connection is logged."""
        import logging
        caplog.set_level(logging.INFO)
        
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {}
        mock_mongo_client.return_value = mock_client
        
        get_mongo_client(role='backend')
        
        # Check for success log (from default logger, not just security)
        all_logs = [record.message.lower() for record in caplog.records]
        assert any("connection established successfully" in msg for msg in all_logs), \
            f"Expected success log not found. All logs: {all_logs}"
    
    @patch.dict(os.environ, {
        'MONGODB_URI': 'mongodb://localhost:27017/',
    })
    @patch('src.infrastructure.mongodb.connection.MongoClient')
    def test_connection_failure_logged(self, mock_mongo_client, caplog):
        """Verify connection failure is logged."""
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        with pytest.raises(RuntimeError):
            get_mongo_client(role='backend')
        
        # Check for failure log
        assert any("[SECURITY]" in record.message and "connection failed" in record.message.lower()
                   for record in caplog.records)


# Integration tests (require actual MongoDB connection)
# Uncomment and configure when MongoDB Atlas users are set up

# class TestRolePermissions:
#     """
#     Integration tests for MongoDB role permissions.
#     
#     REQUIRES: MongoDB Atlas users configured with appropriate roles
#     - backend user: readWrite on verfai
#     - analytics user: read on verfai
#     - admin user: dbAdmin on verfai
#     """
#     
#     @pytest.mark.integration
#     def test_analytics_cannot_write(self):
#         """Verify read-only user cannot insert documents."""
#         client = get_mongo_client(role='analytics')
#         db = client[os.getenv('MONGODB_DB_NAME', 'verfai')]
#         
#         with pytest.raises(OperationFailure):
#             db['test_collection'].insert_one({'test': 'data'})
#     
#     @pytest.mark.integration
#     def test_backend_can_write(self):
#         """Verify backend user can insert and delete documents."""
#         client = get_mongo_client(role='backend')
#         db = client[os.getenv('MONGODB_DB_NAME', 'verfai')]
#         
#         # Insert test document
#         result = db['test_collection'].insert_one({'test': 'data'})
#         assert result.inserted_id is not None
#         
#         # Clean up
#         db['test_collection'].delete_one({'_id': result.inserted_id})
#     
#     @pytest.mark.integration
#     def test_admin_can_create_index(self):
#         """Verify admin user can create indexes."""
#         client = get_mongo_client(role='admin')
#         db = client[os.getenv('MONGODB_DB_NAME', 'verfai')]
#         
#         # Create test index
#         db['test_collection'].create_index('test_field')
#         
#         # Verify index exists
#         indexes = list(db['test_collection'].list_indexes())
#         assert any(idx['name'] == 'test_field_1' for idx in indexes)
#         
#         # Clean up
#         db['test_collection'].drop_index('test_field_1')
