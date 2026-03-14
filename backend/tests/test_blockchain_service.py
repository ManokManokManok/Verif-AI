"""
Phase 3 Tests - Blockchain Service Layer

Run: python tests/test_blockchain_service.py

Requirements:
    - Ganache running on port 7545
    - Contract deployed (see contracts/README.md)
    - Environment configured (.env)
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime
import uuid

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')


class TestBlockchainServiceUnit(unittest.TestCase):
    """Unit tests for blockchain service (no chain connection)."""
    
    def test_import_service(self):
        """Test that service module can be imported."""
        from src.infrastructure.blockchain.service import (
            BlockchainService,
            get_blockchain_service,
            _uuid_to_bytes32,
            _bytes32_to_uuid,
            _timestamp_to_unix,
            _scam_class_to_uint8,
            _uint8_to_scam_class
        )
        self.assertIsNotNone(BlockchainService)
    
    def test_uuid_to_bytes32_conversion(self):
        """Test UUID to bytes32 conversion."""
        from src.infrastructure.blockchain.service import _uuid_to_bytes32, _bytes32_to_uuid
        
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        # Convert to bytes32
        b32 = _uuid_to_bytes32(test_uuid)
        self.assertEqual(len(b32), 32)
        
        # Convert back
        restored = _bytes32_to_uuid(b32)
        self.assertEqual(restored.lower(), test_uuid.lower())
    
    def test_timestamp_conversion(self):
        """Test ISO timestamp to Unix conversion."""
        from src.infrastructure.blockchain.service import _timestamp_to_unix
        
        # Test with milliseconds
        ts = _timestamp_to_unix("2026-01-26T10:30:00.000Z")
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)
        
        # Test without milliseconds
        ts2 = _timestamp_to_unix("2026-01-26T10:30:00Z")
        self.assertEqual(ts, ts2)
    
    def test_scam_class_conversion(self):
        """Test scam class to uint8 conversion."""
        from src.infrastructure.blockchain.service import _scam_class_to_uint8, _uint8_to_scam_class
        
        # Test normal values
        for i in range(15):
            self.assertEqual(_scam_class_to_uint8(i), i)
            self.assertEqual(_uint8_to_scam_class(i), i)
        
        # Test -1 (unknown)
        self.assertEqual(_scam_class_to_uint8(-1), 255)
        self.assertEqual(_uint8_to_scam_class(255), -1)
    
    def test_service_singleton(self):
        """Test that get_blockchain_service returns singleton."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        
        service1 = get_blockchain_service()
        service2 = get_blockchain_service()
        
        self.assertIs(service1, service2)
    
    def test_service_is_enabled_property(self):
        """Test is_enabled property."""
        from src.infrastructure.blockchain.service import BlockchainService
        
        service = BlockchainService()
        # is_enabled depends on CHAIN_ENABLED env var
        self.assertIsInstance(service.is_enabled, bool)
    
    def test_create_chain_metadata(self):
        """Test ChainMetadata creation."""
        from src.infrastructure.blockchain.service import BlockchainService
        from src.infrastructure.blockchain.canonical import CanonicalPayload
        
        service = BlockchainService()
        
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550
        )
        
        metadata = service.create_chain_metadata(
            payload=payload,
            tx_hash="0x1234567890abcdef",
            block_number=42
        )
        
        self.assertEqual(metadata.schema_version, 1)
        self.assertEqual(metadata.chain_tx_hash, "0x1234567890abcdef")
        self.assertEqual(metadata.block_number, 42)
        self.assertIsNotNone(metadata.payload_hash)


class TestBlockchainServiceIntegration(unittest.TestCase):
    """
    Integration tests requiring Ganache connection.
    
    These tests only run if CHAIN_ENABLED=true and Ganache is available.
    """
    
    @classmethod
    def setUpClass(cls):
        """Check if integration tests can run."""
        from src.infrastructure.blockchain.config import get_blockchain_config
        
        cls.config = get_blockchain_config()
        cls.can_run = cls.config.enabled and cls.config.is_valid()
        
        if not cls.can_run:
            print("\n⚠️  Skipping integration tests (blockchain not configured)")
            print("   Set CHAIN_ENABLED=true and configure other CHAIN_* vars")
    
    def setUp(self):
        """Skip if can't run integration tests."""
        if not self.can_run:
            self.skipTest("Blockchain not configured for integration tests")
    
    def test_connection(self):
        """Test connection to Ganache."""
        from src.infrastructure.blockchain.service import BlockchainService
        
        service = BlockchainService()
        service._connect()
        
        self.assertTrue(service._connected)
        self.assertIsNotNone(service._web3)
        self.assertIsNotNone(service._contract)
        self.assertIsNotNone(service._account)
    
    def test_get_owner(self):
        """Test getting contract owner."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        
        service = get_blockchain_service()
        owner = service.get_owner()
        
        self.assertTrue(owner.startswith('0x'))
        self.assertEqual(len(owner), 42)  # 0x + 40 hex chars
    
    def test_get_record_count(self):
        """Test getting record count."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        
        service = get_blockchain_service()
        count = service.get_record_count()
        
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
    
    def test_anchor_and_verify(self):
        """Test full anchor and verify flow."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        from src.infrastructure.blockchain.canonical import CanonicalPayload
        
        service = get_blockchain_service()
        
        # Create unique payload
        ref_id = str(uuid.uuid4())
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1-test",
            ref_id=ref_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=5,
            confidence_bps=7500
        )
        
        # Anchor
        result = service.anchor_analysis(payload)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['tx_hash'])
        self.assertIsNotNone(result['payload_hash'])
        self.assertIsNotNone(result['block_number'])
        print(f"\n   Anchored: tx_hash={result['tx_hash'][:20]}...")
        
        # Verify
        verify_result = service.verify_analysis(payload)
        
        self.assertTrue(verify_result['verified'])
        self.assertTrue(verify_result['on_chain_exists'])
        self.assertEqual(verify_result['on_chain_data']['scam_class'], 5)
        self.assertEqual(verify_result['on_chain_data']['confidence_bps'], 7500)
        print(f"   Verified: scam_class={verify_result['on_chain_data']['scam_class']}")
    
    def test_record_exists(self):
        """Test record existence check."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        from src.infrastructure.blockchain.canonical import CanonicalPayload, compute_payload_hash
        
        service = get_blockchain_service()
        
        # Create and anchor a new payload
        ref_id = str(uuid.uuid4())
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="stub",
            analyzer_version="test",
            ref_id=ref_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=0,
            confidence_bps=5000
        )
        
        payload_hash = compute_payload_hash(payload)
        
        # Should not exist yet
        self.assertFalse(service.record_exists(payload_hash))
        
        # Anchor it
        service.anchor_analysis(payload)
        
        # Now should exist
        self.assertTrue(service.record_exists(payload_hash))
    
    def test_get_record(self):
        """Test getting a specific record."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        from src.infrastructure.blockchain.canonical import CanonicalPayload, compute_payload_hash
        
        service = get_blockchain_service()
        
        # Create and anchor
        ref_id = str(uuid.uuid4())
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="rules",
            analyzer_version="v2",
            ref_id=ref_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=10,
            confidence_bps=9000
        )
        
        service.anchor_analysis(payload)
        payload_hash = compute_payload_hash(payload)
        
        # Get record
        record = service.get_record(payload_hash)
        
        self.assertIsNotNone(record)
        self.assertTrue(record['exists'])
        self.assertEqual(record['scam_class'], 10)
        self.assertEqual(record['confidence_bps'], 9000)
    
    def test_duplicate_anchor_detected_via_events(self):
        """Test that duplicate anchoring is detected via event logs."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        from src.infrastructure.blockchain.canonical import CanonicalPayload, compute_payload_hash
        
        service = get_blockchain_service()
        
        # Create unique payload
        ref_id = str(uuid.uuid4())
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id=ref_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=3,
            confidence_bps=6000
        )
        
        # First anchor should succeed
        result1 = service.anchor_analysis(payload)
        self.assertTrue(result1['success'])
        
        # Backend can detect duplicates via record_exists before sending tx
        payload_hash = compute_payload_hash(payload)
        self.assertTrue(service.record_exists(payload_hash))
    
    def test_verify_nonexistent_record(self):
        """Test verifying a record that doesn't exist."""
        from src.infrastructure.blockchain.service import get_blockchain_service
        from src.infrastructure.blockchain.canonical import CanonicalPayload
        
        service = get_blockchain_service()
        
        # Create payload but don't anchor it
        ref_id = str(uuid.uuid4())
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="stub",
            analyzer_version="v1",
            ref_id=ref_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=0,
            confidence_bps=5000
        )
        
        # Verify should return not found
        result = service.verify_analysis(payload)
        
        self.assertFalse(result['verified'])
        self.assertFalse(result['on_chain_exists'])


def run_tests():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 60)
    print("  PHASE 3 TESTS - Blockchain Service Layer")
    print("=" * 60 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainServiceUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainServiceIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL PHASE 3 TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())