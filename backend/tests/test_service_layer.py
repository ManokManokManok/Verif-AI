"""
Phase 3 Integration Test Script

This script tests the blockchain service with a live Ganache connection.
It sets up the environment variables and runs integration tests.

Usage:
    python scripts/test_phase3_integration.py

Prerequisites:
    1. Ganache running on port 7545
    2. Contract deployed (npm run deploy in contracts/)
    3. Copy private key from Ganache first account
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')


def prompt_for_config():
    """Prompt user for blockchain configuration."""
    print("\n" + "=" * 60)
    print("  PHASE 3 INTEGRATION TEST - Configuration")
    print("=" * 60)
    
    # Check if Ganache is reachable
    try:
        import requests
        response = requests.post(
            "http://127.0.0.1:7545",
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
            timeout=5
        )
        if response.status_code == 200:
            print("\n✅ Ganache is running on port 7545")
        else:
            print("\n❌ Ganache responded but with error")
            return None
    except Exception as e:
        print(f"\n❌ Cannot connect to Ganache: {e}")
        print("   Please start Ganache and try again")
        return None
    
    # Get contract address
    default_contract = "0x7d03703185cA5E0EEDc431bf87FE2423dbea0D17"
    print(f"\nContract address (default: {default_contract}):")
    contract_input = input("  > ").strip()
    contract_address = contract_input if contract_input else default_contract
    
    # Get private key
    print("\nPrivate key from Ganache (click key icon next to first account):")
    print("  (Paste full key starting with 0x, input will be hidden)")
    private_key = input("  > ").strip()
    
    if not private_key:
        print("❌ Private key is required")
        return None
    
    if not private_key.startswith('0x'):
        private_key = f'0x{private_key}'
    
    return {
        'CHAIN_ENABLED': 'true',
        'CHAIN_NETWORK': 'ganache',
        'CHAIN_RPC_URL': 'http://127.0.0.1:7545',
        'CHAIN_CONTRACT_ADDRESS': contract_address,
        'CHAIN_PRIVATE_KEY': private_key,
        'CHAIN_NETWORK_ID': '5777',
        'CHAIN_GAS_LIMIT': '500000'
    }


def run_integration_tests(config: dict):
    """Run integration tests with the provided configuration."""
    # Set environment variables
    for key, value in config.items():
        os.environ[key] = value
    
    # Clear the singleton so it picks up new config
    import src.infrastructure.blockchain.service as service_module
    service_module._blockchain_service = None
    
    print("\n" + "=" * 60)
    print("  Running Integration Tests")
    print("=" * 60)
    
    from src.infrastructure.blockchain.service import get_blockchain_service
    from src.infrastructure.blockchain.canonical import CanonicalPayload, compute_payload_hash
    from src.domain.analysis_entities import ContractError
    
    tests_passed = 0
    tests_failed = 0
    
    service = get_blockchain_service()
    
    # Test 1: Connection
    print("\n1. Testing connection...")
    try:
        service._connect()
        print(f"   ✅ Connected to {service.network_name}")
        print(f"   Account: {service._account.address}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        tests_failed += 1
        return tests_passed, tests_failed
    
    # Test 2: Get owner
    print("\n2. Testing get_owner()...")
    try:
        owner = service.get_owner()
        print(f"   ✅ Contract owner: {owner}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 3: Get record count
    print("\n3. Testing get_record_count()...")
    try:
        count = service.get_record_count()
        print(f"   ✅ Record count: {count}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 4: Anchor analysis
    print("\n4. Testing anchor_analysis()...")
    try:
        ref_id = str(uuid.uuid4())
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1-integration-test",
            ref_id=ref_id,
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=7,
            confidence_bps=8500
        )
        
        result = service.anchor_analysis(payload)
        
        assert result['success'], "Anchor should succeed"
        assert result['tx_hash'], "Should have tx_hash"
        assert result['block_number'], "Should have block_number"
        
        print(f"   ✅ Anchored successfully!")
        print(f"      tx_hash: {result['tx_hash'][:30]}...")
        print(f"      block: {result['block_number']}")
        print(f"      gas_used: {result['gas_used']}")
        tests_passed += 1
        
        # Store for verification test
        anchored_payload = payload
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
        anchored_payload = None
    
    # Test 5: Verify analysis
    if anchored_payload:
        print("\n5. Testing verify_analysis()...")
        try:
            result = service.verify_analysis(anchored_payload)
            
            assert result['verified'], "Should be verified"
            assert result['on_chain_exists'], "Should exist on chain"
            assert result['on_chain_data']['scam_class'] == 7
            assert result['on_chain_data']['confidence_bps'] == 8500
            
            print(f"   ✅ Verified successfully!")
            print(f"      on_chain scam_class: {result['on_chain_data']['scam_class']}")
            print(f"      on_chain confidence: {result['on_chain_data']['confidence_bps']}")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            tests_failed += 1
    
    # Test 6: Get record
    if anchored_payload:
        print("\n6. Testing get_record()...")
        try:
            payload_hash = compute_payload_hash(anchored_payload)
            record = service.get_record(payload_hash)
            
            assert record is not None
            assert record['exists']
            
            print(f"   ✅ Record retrieved!")
            print(f"      ref_id: {record['ref_id']}")
            print(f"      stored_by: {record['stored_by']}")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            tests_failed += 1
    
    # Test 7: Duplicate anchor fails
    if anchored_payload:
        print("\n7. Testing duplicate anchor rejection...")
        try:
            service.anchor_analysis(anchored_payload)
            print(f"   ❌ Should have rejected duplicate!")
            tests_failed += 1
        except ContractError as e:
            print(f"   ✅ Duplicate correctly rejected")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ Wrong error type: {e}")
            tests_failed += 1
    
    # Test 8: Record exists
    if anchored_payload:
        print("\n8. Testing record_exists()...")
        try:
            payload_hash = compute_payload_hash(anchored_payload)
            exists = service.record_exists(payload_hash)
            assert exists, "Record should exist"
            
            # Check non-existent
            fake_hash = "0x" + "a" * 64
            not_exists = service.record_exists(fake_hash)
            assert not not_exists, "Fake hash should not exist"
            
            print(f"   ✅ record_exists() works correctly")
            tests_passed += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            tests_failed += 1
    
    # Test 9: Verify non-existent record
    print("\n9. Testing verify of non-existent record...")
    try:
        new_payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="stub",
            analyzer_version="v1",
            ref_id=str(uuid.uuid4()),
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            scam_class=0,
            confidence_bps=5000
        )
        
        result = service.verify_analysis(new_payload)
        
        assert not result['verified']
        assert not result['on_chain_exists']
        
        print(f"   ✅ Correctly returns not verified for non-existent")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  PHASE 3 INTEGRATION TEST")
    print("  Blockchain Service Layer")
    print("=" * 60)
    
    # Check for existing config or prompt
    from src.infrastructure.blockchain.config import get_blockchain_config
    
    config = get_blockchain_config()
    
    if config.enabled and config.is_valid():
        print("\n✅ Using existing configuration from environment")
        env_config = {
            'CHAIN_ENABLED': 'true',
            'CHAIN_NETWORK': config.network_name,
            'CHAIN_RPC_URL': config.rpc_url,
            'CHAIN_CONTRACT_ADDRESS': config.contract_address,
            'CHAIN_PRIVATE_KEY': config.private_key,
        }
        tests_passed, tests_failed = run_integration_tests(env_config)
    else:
        # Prompt for configuration
        env_config = prompt_for_config()
        
        if env_config is None:
            print("\n❌ Configuration cancelled")
            return 1
        
        tests_passed, tests_failed = run_integration_tests(env_config)
    
    # Summary
    print("\n" + "=" * 60)
    print("  INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"  Tests Passed: {tests_passed}")
    print(f"  Tests Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n✅ ALL PHASE 3 INTEGRATION TESTS PASSED!")
        print("\nPhase 3 is COMPLETE. The blockchain service layer is working.")
        print("\nNext steps:")
        print("  1. Update .env with the configuration")
        print("  2. Proceed to Phase 4: DB Chain Linkage")
        return 0
    else:
        print(f"\n❌ {tests_failed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())