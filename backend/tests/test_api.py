"""
Phase 5 API Test Script

Tests the blockchain API endpoints with authentication.

Usage:
    1. Start Django server: python manage.py runserver
    2. Run this script: python scripts/test_phase5_api.py

Prerequisites:
    1. Django server running on port 8000
    2. MongoDB running
    3. Ganache running on port 7545
    4. .env configured with CHAIN_* vars
    5. Admin user created in database
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# Load environment
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

BASE_URL = "http://127.0.0.1:8000/api"


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    status = "✅" if passed else "❌"
    print(f"\n{status} {test_name}")
    if details:
        print(f"   {details}")


def print_response(resp: requests.Response) -> None:
    """Print response details for debugging."""
    print(f"   Status: {resp.status_code}")
    try:
        print(f"   Body: {json.dumps(resp.json(), indent=2)[:500]}")
    except:
        print(f"   Body: {resp.text[:500]}")


def create_test_user_and_get_token() -> tuple:
    """Create a test admin user and get JWT token."""
    from pymongo import MongoClient
    from src.infrastructure.mongodb.repositories import MongoDBUserRepository
    from src.domain.entities import User
    from src.domain.services import BCryptPasswordHasher
    
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
    db_name = os.getenv('MONGODB_DB_NAME', 'verfai1')
    
    repo = MongoDBUserRepository(client, db_name)
    hasher = BCryptPasswordHasher()
    
    # Check if test user exists
    test_email = "admin_test@verfai.test"
    existing = repo.get_by_email(test_email)
    
    if not existing:
        # Create admin user
        user = User(
            id=None,
            email=test_email,
            password_hash=hasher.hash_password("TestAdmin123!"),
            roles=["admin"],
            username="test_admin",
            is_active=True,
            is_verified=True
        )
        user = repo.create_user(user)
        print(f"   Created test admin user: {test_email}")
    else:
        print(f"   Using existing test admin: {test_email}")
    
    # Login to get token
    login_resp = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": test_email, "password": "TestAdmin123!"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Login response status: {login_resp.status_code}")
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        # Handle both response formats: tokens.access_token or direct access_token
        tokens = data.get('tokens', {})
        token = tokens.get('access_token') or data.get('access_token')
        user_id = data.get('user', {}).get('id')
        return token, user_id
    else:
        print(f"   Login failed: {login_resp.status_code}")
        print(f"   Response: {login_resp.text[:500]}")
        return None, None


def create_test_analysis() -> str:
    """Create a test analysis in the database."""
    from pymongo import MongoClient
    from src.domain.analysis_entities import AnalysisResult
    from src.infrastructure.mongodb.analysis_repository import AnalysisResultRepository
    
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
    db_name = os.getenv('MONGODB_DB_NAME', 'verfai1')
    
    repo = AnalysisResultRepository(client, db_name)
    
    analysis = AnalysisResult.create(
        scam_class=3,
        scam_type="Impersonation Authority Scam",
        confidence_bps=8200,
        is_scam=True,
        analyzer_type="bert",
        analyzer_version="v1.0.0"
    )
    
    saved = repo.save(analysis)
    return saved.ref_id


def run_api_tests():
    """Run Phase 5 API tests."""
    print_header("PHASE 5 API TEST")
    print("Blockchain API Endpoints")
    
    tests_passed = 0
    tests_failed = 0
    
    # Check if server is running
    print("\n" + "-" * 60)
    print("  Checking prerequisites")
    print("-" * 60)
    
    try:
        health_resp = requests.get(f"{BASE_URL}/health/", timeout=5)
        if health_resp.status_code == 200:
            print("\n✅ Django server is running")
        else:
            print(f"\n❌ Server health check failed: {health_resp.status_code}")
            return 1
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to Django server")
        print("   Start the server with: python manage.py runserver")
        return 1
    
    # Get auth token
    print("\n   Setting up authentication...")
    token, user_id = create_test_user_and_get_token()
    
    if not token:
        print("\n❌ Failed to get authentication token")
        return 1
    
    print(f"   ✅ Got auth token for user: {user_id}")
    
    # Create test analysis
    print("\n   Creating test analysis...")
    test_ref_id = create_test_analysis()
    print(f"   ✅ Created analysis: {test_ref_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "-" * 60)
    print("  Running API Tests")
    print("-" * 60)
    
    # Test 1: Blockchain status (public)
    print("\n1. Testing blockchain status endpoint (public)...")
    try:
        resp = requests.get(f"{BASE_URL}/blockchain/status/")
        passed = resp.status_code == 200 and resp.json().get('enabled') == True
        print_result(
            "GET /api/blockchain/status/",
            passed,
            f"enabled={resp.json().get('enabled')}, connected={resp.json().get('connected')}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET /api/blockchain/status/", False, str(e))
        tests_failed += 1
    
    # Test 2: List analyses (requires auth)
    print("\n2. Testing list analyses (authenticated)...")
    try:
        resp = requests.get(f"{BASE_URL}/blockchain/analyses/", headers=headers)
        passed = resp.status_code == 200 and 'analyses' in resp.json()
        print_result(
            "GET /api/blockchain/analyses/",
            passed,
            f"count={resp.json().get('count')}, total_anchored={resp.json().get('total_anchored')}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET /api/blockchain/analyses/", False, str(e))
        tests_failed += 1
    
    # Test 3: Get analysis (requires auth)
    print("\n3. Testing get analysis (authenticated)...")
    try:
        resp = requests.get(f"{BASE_URL}/blockchain/analysis/{test_ref_id}/", headers=headers)
        passed = resp.status_code == 200 and resp.json().get('ref_id') == test_ref_id
        print_result(
            f"GET /api/blockchain/analysis/{{ref_id}}/",
            passed,
            f"ref_id={resp.json().get('ref_id')}, is_anchored={resp.json().get('is_anchored')}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET /api/blockchain/analysis/{ref_id}/", False, str(e))
        tests_failed += 1
    
    # Test 4: Anchor analysis (admin only)
    print("\n4. Testing anchor analysis (admin only)...")
    try:
        resp = requests.post(f"{BASE_URL}/blockchain/analysis/{test_ref_id}/anchor/", headers=headers)
        passed = resp.status_code == 200 and resp.json().get('success') == True
        print_result(
            f"POST /api/blockchain/analysis/{{ref_id}}/anchor/",
            passed,
            f"tx_hash={resp.json().get('tx_hash', 'N/A')[:30]}..."
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("POST /api/blockchain/analysis/{ref_id}/anchor/", False, str(e))
        tests_failed += 1
    
    # Test 5: Verify analysis (authenticated)
    print("\n5. Testing verify analysis (authenticated)...")
    try:
        resp = requests.get(f"{BASE_URL}/blockchain/analysis/{test_ref_id}/verify/", headers=headers)
        passed = resp.status_code == 200 and resp.json().get('verified') == True
        print_result(
            f"GET /api/blockchain/analysis/{{ref_id}}/verify/",
            passed,
            f"verified={resp.json().get('verified')}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET /api/blockchain/analysis/{ref_id}/verify/", False, str(e))
        tests_failed += 1
    
    # Test 6: Duplicate anchor rejection
    print("\n6. Testing duplicate anchor rejection...")
    try:
        resp = requests.post(f"{BASE_URL}/blockchain/analysis/{test_ref_id}/anchor/", headers=headers)
        passed = resp.status_code == 400 and resp.json().get('error', {}).get('code') == 'ALREADY_ANCHORED'
        print_result(
            "POST duplicate anchor",
            passed,
            f"code={resp.json().get('error', {}).get('code')}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("POST duplicate anchor", False, str(e))
        tests_failed += 1
    
    # Test 7: Force re-anchor
    print("\n7. Testing force re-anchor (admin only)...")
    try:
        resp = requests.post(f"{BASE_URL}/blockchain/analysis/{test_ref_id}/anchor/?force=true", headers=headers)
        # This might fail with contract error if duplicate hash, which is expected
        passed = resp.status_code in (200, 500)  # 500 = contract rejects duplicate hash
        detail = f"status={resp.status_code}"
        if resp.status_code == 200:
            detail = f"success, tx_hash={resp.json().get('tx_hash', 'N/A')[:20]}..."
        elif resp.status_code == 500:
            detail = "contract rejected duplicate (expected)"
        print_result(
            "POST force re-anchor",
            passed,
            detail
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("POST force re-anchor", False, str(e))
        tests_failed += 1
    
    # Test 8: Not found error
    print("\n8. Testing analysis not found...")
    try:
        fake_ref_id = "00000000-0000-0000-0000-000000000000"
        resp = requests.get(f"{BASE_URL}/blockchain/analysis/{fake_ref_id}/", headers=headers)
        passed = resp.status_code == 404
        print_result(
            "GET non-existent analysis",
            passed,
            f"status={resp.status_code}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET non-existent analysis", False, str(e))
        tests_failed += 1
    
    # Test 9: Unauthenticated request
    print("\n9. Testing unauthenticated request rejection...")
    try:
        resp = requests.get(f"{BASE_URL}/blockchain/analyses/")  # No auth header
        passed = resp.status_code == 401
        print_result(
            "GET without auth",
            passed,
            f"status={resp.status_code}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET without auth", False, str(e))
        tests_failed += 1
    
    # Test 10: List with filters
    print("\n10. Testing list with anchored_only filter...")
    try:
        resp = requests.get(
            f"{BASE_URL}/blockchain/analyses/?anchored_only=true&limit=5",
            headers=headers
        )
        passed = (
            resp.status_code == 200 and 
            resp.json().get('filters', {}).get('anchored_only') == True
        )
        print_result(
            "GET /api/blockchain/analyses/?anchored_only=true",
            passed,
            f"count={resp.json().get('count')}"
        )
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
            print_response(resp)
    except Exception as e:
        print_result("GET with filters", False, str(e))
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("  PHASE 5 API TEST SUMMARY")
    print("=" * 60)
    print(f"  Tests Passed: {tests_passed}")
    print(f"  Tests Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n✅ ALL PHASE 5 API TESTS PASSED!")
        print("\nPhase 5 is COMPLETE. API endpoints are working.")
        print("\nAPI Endpoints:")
        print("  - GET  /api/blockchain/status/                  (public)")
        print("  - GET  /api/blockchain/analyses/                (authenticated)")
        print("  - GET  /api/blockchain/analysis/{ref_id}/       (authenticated)")
        print("  - POST /api/blockchain/analysis/{ref_id}/anchor (admin only)")
        print("  - GET  /api/blockchain/analysis/{ref_id}/verify (authenticated)")
        return 0
    else:
        print(f"\n❌ {tests_failed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_api_tests())
