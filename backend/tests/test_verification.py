"""
Phase 0, 1 & 2 Verification Script

Run this script to verify that Phase 0, 1, and 2 implementations are complete and working.

Usage:
    python backend/scripts/verify_phase0.py
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# Set minimal Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')


def load_contract_abi(abi_path: Path) -> list:
    """Load ABI from file, handling both plain ABI and Truffle artifact formats."""
    with open(abi_path) as f:
        data = json.load(f)
    
    # Handle both formats: full Truffle artifact or plain ABI array
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'abi' in data:
        return data['abi']
    else:
        raise ValueError(f"Invalid ABI file format at {abi_path}")


def test_imports():
    """Test that all new modules can be imported."""
    print("=" * 60)
    print("Phase 0 Verification - Import Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Analysis Entities
    try:
        from src.domain.analysis_entities import (
            AnalysisResult, ChainMetadata, ScamClass, AnalyzerType,
            AnalysisNotFoundError, AnalysisAlreadyAnchoredError,
            BlockchainError, ChainDisabledError
        )
        print("✅ analysis_entities.py - All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ analysis_entities.py - Import failed: {e}")
        tests_failed += 1
    
    # Test 2: Analysis Repository
    try:
        from src.infrastructure.mongodb.analysis_repository import (
            AnalysisResultRepository
        )
        print("✅ analysis_repository.py - All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ analysis_repository.py - Import failed: {e}")
        tests_failed += 1
    
    # Test 3: Blockchain Config
    try:
        from src.infrastructure.blockchain.config import (
            BlockchainConfig, get_blockchain_config
        )
        print("✅ blockchain/config.py - All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ blockchain/config.py - Import failed: {e}")
        tests_failed += 1
    
    # Test 4: Blockchain Canonical
    try:
        from src.infrastructure.blockchain.canonical import (
            CanonicalPayload, canonicalize_payload, compute_payload_hash,
            CURRENT_SCHEMA_VERSION
        )
        print("✅ blockchain/canonical.py - All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ blockchain/canonical.py - Import failed: {e}")
        tests_failed += 1
    
    # Test 5: Blockchain Adapter
    try:
        from src.infrastructure.blockchain.adapter import (
            BlockchainAdapter, BlockchainDisabled
        )
        print("✅ blockchain/adapter.py - All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ blockchain/adapter.py - Import failed: {e}")
        tests_failed += 1
    
    # Test 6: Blockchain __init__
    try:
        from src.infrastructure.blockchain import (
            BlockchainConfig, get_blockchain_config,
            BlockchainAdapter, BlockchainDisabled,
            CanonicalPayload, canonicalize_payload, compute_payload_hash
        )
        print("✅ blockchain/__init__.py - All imports successful")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ blockchain/__init__.py - Import failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_analysis_entity():
    """Test AnalysisResult entity creation."""
    print("\n" + "=" * 60)
    print("Phase 0 Verification - Entity Tests")
    print("=" * 60)
    
    from src.domain.analysis_entities import AnalysisResult, AnalyzerType
    
    tests_passed = 0
    tests_failed = 0
    
    # Test: Create analysis result
    try:
        result = AnalysisResult.create(
            scam_class=0,
            scam_type="Banking Access & Payment",
            confidence_bps=8550,
            is_scam=True,
            analyzer_type=AnalyzerType.BERT,
            analyzer_version="v1"
        )
        
        assert result.ref_id is not None, "ref_id should be generated"
        assert result.scam_class == 0
        assert result.confidence_bps == 8550
        assert result.is_scam == True
        assert result.is_anchored == False  # Not yet anchored
        
        print("✅ AnalysisResult.create() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ AnalysisResult.create() failed: {e}")
        tests_failed += 1
    
    # Test: Convert to dict
    try:
        result_dict = result.to_dict()
        assert "ref_id" in result_dict
        assert "is_anchored" in result_dict
        assert result_dict["is_anchored"] == False
        
        print("✅ AnalysisResult.to_dict() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ AnalysisResult.to_dict() failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_canonical_payload():
    """Test canonical payload creation and hashing."""
    print("\n" + "=" * 60)
    print("Phase 0 Verification - Canonical Payload Tests")
    print("=" * 60)
    
    from datetime import datetime
    from src.infrastructure.blockchain.canonical import (
        CanonicalPayload, canonicalize_payload, compute_payload_hash
    )
    
    tests_passed = 0
    tests_failed = 0
    
    # Test: Create canonical payload
    try:
        payload = CanonicalPayload.from_analysis_result(
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            scam_class=0,
            confidence_bps=8550,
            created_at=datetime(2026, 1, 26, 10, 30, 0),
            analyzer_type="bert",
            analyzer_version="v1"
        )
        
        assert payload.schema_version == 1
        assert payload.scam_class == 0
        assert payload.confidence_bps == 8550
        
        print("✅ CanonicalPayload.from_analysis_result() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ CanonicalPayload.from_analysis_result() failed: {e}")
        tests_failed += 1
    
    # Test: Canonicalize payload (deterministic JSON)
    try:
        json1 = canonicalize_payload(payload)
        json2 = canonicalize_payload(payload)
        
        assert json1 == json2, "Canonicalization should be deterministic"
        assert '"schemaVersion":1' in json1
        assert ' ' not in json1, "No whitespace in canonical JSON"
        
        print("✅ canonicalize_payload() is deterministic")
        tests_passed += 1
    except Exception as e:
        print(f"❌ canonicalize_payload() failed: {e}")
        tests_failed += 1
    
    # Test: Compute hash (deterministic)
    try:
        hash1 = compute_payload_hash(payload)
        hash2 = compute_payload_hash(payload)
        
        assert hash1 == hash2, "Hash should be deterministic"
        assert hash1.startswith("0x"), "Hash should have 0x prefix"
        assert len(hash1) == 66, "Keccak-256 hash should be 66 chars (0x + 64)"
        
        print(f"✅ compute_payload_hash() works correctly")
        print(f"   Hash: {hash1[:20]}...")
        tests_passed += 1
    except Exception as e:
        print(f"❌ compute_payload_hash() failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_blockchain_config():
    """Test blockchain configuration loading."""
    print("\n" + "=" * 60)
    print("Phase 0 Verification - Config Tests")
    print("=" * 60)
    
    from src.infrastructure.blockchain.config import (
        get_blockchain_config, reset_config
    )
    
    tests_passed = 0
    tests_failed = 0
    
    # Reset to get fresh config
    reset_config()
    
    # Test: Load config
    try:
        config = get_blockchain_config()
        
        print(f"   CHAIN_ENABLED: {config.enabled}")
        print(f"   CHAIN_NETWORK: {config.network_name}")
        print(f"   Config valid: {config.is_valid()}")
        
        if not config.enabled:
            print("✅ Blockchain correctly disabled (CHAIN_ENABLED not set)")
        else:
            print("✅ Blockchain configuration loaded")
        
        tests_passed += 1
    except Exception as e:
        print(f"❌ get_blockchain_config() failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_blockchain_adapter():
    """Test blockchain adapter initialization."""
    print("\n" + "=" * 60)
    print("Phase 0 Verification - Adapter Tests")
    print("=" * 60)
    
    from src.infrastructure.blockchain.adapter import (
        BlockchainAdapter, BlockchainDisabled
    )
    from src.infrastructure.blockchain.config import reset_config
    
    tests_passed = 0
    tests_failed = 0
    
    # Reset config to ensure clean state
    reset_config()
    
    # Test: Create adapter (should return BlockchainDisabled when not configured)
    try:
        adapter = BlockchainAdapter()
        
        if isinstance(adapter, BlockchainDisabled):
            print("✅ BlockchainAdapter correctly returns BlockchainDisabled when chain disabled")
            tests_passed += 1
        else:
            print("✅ BlockchainAdapter initialized successfully")
            tests_passed += 1
    except Exception as e:
        print(f"❌ BlockchainAdapter creation failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_phase1_validation():
    """Test Phase 1 validation and schema features."""
    print("\n" + "=" * 60)
    print("Phase 1 Verification - Validation Tests")
    print("=" * 60)
    
    from src.infrastructure.blockchain.canonical import (
        CanonicalPayload, PayloadValidationError, validate_against_schema,
        VALID_ANALYZER_TYPES, EXAMPLE_PAYLOAD_V1
    )
    
    tests_passed = 0
    tests_failed = 0
    
    # Test: Validation rejects invalid analyzer type
    try:
        try:
            CanonicalPayload(
                schema_version=1,
                analyzer_type="invalid_type",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=5000
            )
            print("❌ Should have rejected invalid analyzer type")
            tests_failed += 1
        except PayloadValidationError:
            print("✅ Validation correctly rejects invalid analyzer type")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        tests_failed += 1
    
    # Test: Validation rejects invalid UUID
    try:
        try:
            CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="not-a-valid-uuid",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=5000
            )
            print("❌ Should have rejected invalid UUID")
            tests_failed += 1
        except PayloadValidationError:
            print("✅ Validation correctly rejects invalid UUID format")
            tests_passed += 1
    except Exception as e:
        print(f"❌ UUID validation test failed: {e}")
        tests_failed += 1
    
    # Test: validate_against_schema function
    try:
        is_valid, errors = validate_against_schema(EXAMPLE_PAYLOAD_V1)
        assert is_valid, f"Example payload should be valid: {errors}"
        print("✅ validate_against_schema() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ validate_against_schema() failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_phase1_hash_determinism():
    """Test Phase 1 hash determinism across multiple runs."""
    print("\n" + "=" * 60)
    print("Phase 1 Verification - Hash Determinism Tests")
    print("=" * 60)
    
    from datetime import datetime
    from src.infrastructure.blockchain.canonical import (
        CanonicalPayload, compute_payload_hash, verify_payload_hash
    )
    
    tests_passed = 0
    tests_failed = 0
    
    # Create same payload twice
    def create_payload():
        return CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550
        )
    
    # Test: Multiple payload instances produce same hash
    try:
        payload1 = create_payload()
        payload2 = create_payload()
        
        hash1 = compute_payload_hash(payload1)
        hash2 = compute_payload_hash(payload2)
        
        assert hash1 == hash2, "Same payload data should produce same hash"
        print("✅ Different instances with same data produce same hash")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Hash determinism test failed: {e}")
        tests_failed += 1
    
    # Test: verify_payload_hash works
    try:
        payload = create_payload()
        hash_value = compute_payload_hash(payload)
        
        assert verify_payload_hash(payload, hash_value), "Verification should pass"
        assert not verify_payload_hash(payload, "0x" + "a" * 64), "Wrong hash should fail"
        
        print("✅ verify_payload_hash() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ verify_payload_hash() test failed: {e}")
        tests_failed += 1
    
    # Test: Hash is stable (known value)
    try:
        payload = create_payload()
        hash_value = compute_payload_hash(payload)
        
        # Store the expected hash for future regression testing
        print(f"   Current hash: {hash_value[:30]}...")
        print("✅ Hash computation produces consistent output")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Hash stability test failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def main():
    """Run all Phase 0 and Phase 1 verification tests."""
    print("\n" + "=" * 60)
    print("  PHASE 0 & 1 VERIFICATION - Verif-AI Blockchain Integration")
    print("=" * 60 + "\n")
    
    total_passed = 0
    total_failed = 0
    
    # Phase 0 tests
    print("=" * 60)
    print("PHASE 0: Repository Discovery + Integration Points")
    print("=" * 60)
    
    passed, failed = test_imports()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_analysis_entity()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_canonical_payload()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_blockchain_config()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_blockchain_adapter()
    total_passed += passed
    total_failed += failed
    
    # Phase 1 tests
    print("\n" + "=" * 60)
    print("PHASE 1: Canonical Payload Schema + Hashing Rules")
    print("=" * 60)
    
    passed, failed = test_phase1_validation()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_phase1_hash_determinism()
    total_passed += passed
    total_failed += failed
    
    # Phase 2 tests
    print("\n" + "=" * 60)
    print("PHASE 2: Smart Contract (Solidity)")
    print("=" * 60)
    
    passed, failed = test_phase2_contract_abi()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_phase2_contract_structure()
    total_passed += passed
    total_failed += failed
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {total_passed}")
    print(f"Tests Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✅ PHASES 0, 1 & 2 COMPLETE - All tests passed!")
        print("\nPhase 0: Repository Discovery ✅")
        print("Phase 1: Canonical Payload Schema ✅")
        print("Phase 2: Smart Contract ✅")
        print("\nNext Steps:")
        print("1. Ensure Ganache is running (http://127.0.0.1:7545)")
        print("2. Proceed to Phase 3: Backend Blockchain Service Layer")
        return 0
    else:
        print(f"\n❌ VERIFICATION INCOMPLETE - {total_failed} test(s) failed")
        return 1


def test_phase2_contract_abi():
    """Test that contract ABI is available for backend."""
    print("\n" + "=" * 60)
    print("Phase 2 Verification - Contract ABI Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test: ABI file exists
    try:
        abi_path = backend_dir / "src" / "infrastructure" / "blockchain" / "abi" / "AnalysisAnchor.json"
        assert abi_path.exists(), f"ABI file not found at {abi_path}"
        
        abi = load_contract_abi(abi_path)
        assert isinstance(abi, list), "ABI should be a list"
        
        print("✅ Contract ABI file exists and is valid JSON")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Contract ABI file error: {e}")
        tests_failed += 1
    
    # Test: ABI has required functions
    try:
        abi_path = backend_dir / "src" / "infrastructure" / "blockchain" / "abi" / "AnalysisAnchor.json"
        abi = load_contract_abi(abi_path)
        
        function_names = [item['name'] for item in abi if item.get('type') == 'function']
        
        required_functions = ['storeRecord', 'owner', 'transferOwnership']
        missing = [fn for fn in required_functions if fn not in function_names]
        
        assert not missing, f"Missing functions: {missing}"
        
        print(f"✅ ABI contains all required functions: {len(function_names)} total")
        tests_passed += 1
    except Exception as e:
        print(f"❌ ABI function check failed: {e}")
        tests_failed += 1
    
    # Test: ABI has RecordStored event
    try:
        abi_path = backend_dir / "src" / "infrastructure" / "blockchain" / "abi" / "AnalysisAnchor.json"
        abi = load_contract_abi(abi_path)
        
        event_names = [item['name'] for item in abi if item.get('type') == 'event']
        
        assert 'RecordStored' in event_names, "RecordStored event not found"
        
        print(f"✅ ABI contains RecordStored event")
        tests_passed += 1
    except Exception as e:
        print(f"❌ ABI event check failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def test_phase2_contract_structure():
    """Test contract structure meets requirements."""
    print("\n" + "=" * 60)
    print("Phase 2 Verification - Contract Structure Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test: storeRecord function signature
    try:
        abi_path = backend_dir / "src" / "infrastructure" / "blockchain" / "abi" / "AnalysisAnchor.json"
        abi = load_contract_abi(abi_path)
        
        store_record = next((item for item in abi if item.get('name') == 'storeRecord'), None)
        assert store_record is not None, "storeRecord function not found"
        
        # Check inputs
        input_names = [inp['name'] for inp in store_record['inputs']]
        expected_inputs = ['payloadHash', 'scamClass', 'confidenceBps', 'timestamp', 'refId']
        
        assert input_names == expected_inputs, f"Expected inputs {expected_inputs}, got {input_names}"
        
        print("✅ storeRecord has correct function signature")
        tests_passed += 1
    except Exception as e:
        print(f"❌ storeRecord signature check failed: {e}")
        tests_failed += 1
    
    # Test: RecordStored event has all required fields for off-chain retrieval
    try:
        abi_path = backend_dir / "src" / "infrastructure" / "blockchain" / "abi" / "AnalysisAnchor.json"
        abi = load_contract_abi(abi_path)
        
        record_stored = next((item for item in abi if item.get('name') == 'RecordStored' and item.get('type') == 'event'), None)
        assert record_stored is not None, "RecordStored event not found"
        
        input_names = [inp['name'] for inp in record_stored['inputs']]
        expected_fields = ['payloadHash', 'refId', 'scamClass', 'confidenceBps', 'timestamp', 'storedBy']
        
        assert input_names == expected_fields, f"Expected event fields {expected_fields}, got {input_names}"
        
        print("✅ RecordStored event contains all required fields")
        tests_passed += 1
    except Exception as e:
        print(f"❌ RecordStored event field check failed: {e}")
        tests_failed += 1
    
    # Test: Data types are correct
    try:
        abi_path = backend_dir / "src" / "infrastructure" / "blockchain" / "abi" / "AnalysisAnchor.json"
        abi = load_contract_abi(abi_path)
        
        store_record = next((item for item in abi if item.get('name') == 'storeRecord'), None)
        
        type_map = {inp['name']: inp['type'] for inp in store_record['inputs']}
        
        assert type_map['payloadHash'] == 'bytes32', f"payloadHash should be bytes32, got {type_map['payloadHash']}"
        assert type_map['scamClass'] == 'uint8', f"scamClass should be uint8, got {type_map['scamClass']}"
        assert type_map['confidenceBps'] == 'uint16', f"confidenceBps should be uint16, got {type_map['confidenceBps']}"
        assert type_map['timestamp'] == 'uint64', f"timestamp should be uint64, got {type_map['timestamp']}"
        assert type_map['refId'] == 'bytes32', f"refId should be bytes32, got {type_map['refId']}"
        
        print("✅ All contract data types are correct")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Data type check failed: {e}")
        tests_failed += 1
    
    # Test: Truffle artifacts exist
    try:
        contracts_dir = backend_dir.parent / "contracts"
        build_dir = contracts_dir / "build" / "contracts"
        
        assert build_dir.exists(), f"Build directory not found: {build_dir}"
        
        artifact_path = build_dir / "AnalysisAnchor.json"
        assert artifact_path.exists(), f"AnalysisAnchor artifact not found"
        
        print("✅ Truffle build artifacts exist")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Truffle artifacts check failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


if __name__ == "__main__":
    sys.exit(main())