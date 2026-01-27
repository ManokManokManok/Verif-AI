"""
Phase 6 Frontend Integration Test Script
Tests the blockchain frontend components by verifying API connectivity

Run this after:
1. Backend server is running: python manage.py runserver 8000
2. Ganache is running on localhost:7545
3. Frontend is running: npm run dev (port 5173)

Usage: python scripts/test_phase6_frontend.py
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add the backend src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

BASE_URL = "http://127.0.0.1:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} - {name}")
    if message and not passed:
        print(f"         {Colors.YELLOW}{message}{Colors.RESET}")

def print_section(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f" {title}")
    print(f"{'='*60}{Colors.RESET}\n")

def test_backend_connectivity():
    """Test that backend is running"""
    print_section("Backend Connectivity Tests")
    
    try:
        # Test root endpoint or health
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print_test("Backend is reachable", True)
        return True
    except requests.exceptions.ConnectionError:
        print_test("Backend is reachable", False, "Cannot connect to backend at localhost:8000")
        return False

def test_blockchain_status_endpoint():
    """Test the public blockchain status endpoint"""
    print_section("Blockchain Status Endpoint (Public)")
    
    try:
        response = requests.get(f"{BASE_URL}/blockchain/status/", timeout=10)
        
        # Check status code
        print_test("Status endpoint returns 200", response.status_code == 200, 
                   f"Got {response.status_code}")
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        
        # Check response structure
        print_test("Response has 'connected' field", 'connected' in data)
        print_test("Response has 'network' field", 'network' in data)
        print_test("Response has 'contractAddress' field", 'contractAddress' in data or 'contract_address' in data)
        
        # Check blockchain connection
        is_connected = data.get('connected', False)
        print_test("Blockchain is connected", is_connected,
                   "Ganache may not be running" if not is_connected else "")
        
        print(f"\n  {Colors.YELLOW}Status Details:{Colors.RESET}")
        print(f"    Connected: {data.get('connected')}")
        print(f"    Network: {data.get('network', data.get('networkName', 'N/A'))}")
        print(f"    Contract: {data.get('contractAddress', data.get('contract_address', 'N/A'))}")
        if 'blockNumber' in data or 'block_number' in data:
            print(f"    Block: {data.get('blockNumber', data.get('block_number', 'N/A'))}")
        
        return True
    except requests.exceptions.ConnectionError:
        print_test("Status endpoint accessible", False, "Connection refused")
        return False
    except Exception as e:
        print_test("Status endpoint test", False, str(e))
        return False

def test_analyses_endpoint_unauthenticated():
    """Test that analyses endpoint requires authentication"""
    print_section("Analyses Endpoint (Requires Auth)")
    
    try:
        response = requests.get(f"{BASE_URL}/blockchain/analyses/", timeout=5)
        
        # Should return 401 for unauthenticated
        is_protected = response.status_code == 401
        print_test("Endpoint is protected (401 without auth)", is_protected,
                   f"Got {response.status_code}" if not is_protected else "")
        
        return is_protected
    except requests.exceptions.ConnectionError:
        print_test("Analyses endpoint accessible", False, "Connection refused")
        return False
    except Exception as e:
        print_test("Analyses endpoint test", False, str(e))
        return False

def test_analyses_endpoint_authenticated():
    """Test analyses endpoint with authentication"""
    print_section("Analyses Endpoint (Authenticated)")
    
    try:
        # First, login to get a token using existing test user from Phase 5
        test_email = "admin_test@verfai.test"
        test_password = "TestAdmin123!"
        
        # Login
        login_response = requests.post(
            f"{BASE_URL}/auth/login/",
            json={"email": test_email, "password": test_password}
        )
        
        if login_response.status_code != 200:
            print_test("Login successful", False, f"Got {login_response.status_code} - Run Phase 5 tests first to create admin user")
            return False
            
        login_data = login_response.json()
        token = login_data.get('tokens', {}).get('access_token')
        
        if not token:
            print_test("Got access token", False, "No token in response")
            return False
            
        print_test("Login successful", True)
        
        # Test authenticated request
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/blockchain/analyses/", headers=headers, timeout=5)
        
        print_test("Authenticated request returns 200", response.status_code == 200,
                   f"Got {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_test("Response has 'analyses' field", 'analyses' in data)
            print_test("Response has 'total' field", 'total' in data)
            print(f"\n  {Colors.YELLOW}Analyses count: {data.get('total', 0)}{Colors.RESET}")
        
        return response.status_code == 200
        
    except Exception as e:
        print_test("Authenticated analyses test", False, str(e))
        return False

def test_frontend_files_exist():
    """Verify frontend files were created correctly"""
    print_section("Frontend Files Verification")
    
    frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'src')
    
    files_to_check = [
        ('domain/types/blockchain.ts', 'Blockchain types'),
        ('infrastructure/api/BlockchainApi.ts', 'Blockchain API service'),
        ('interfaces/components/blockchain/VerifyButton.tsx', 'Verify button component'),
        ('interfaces/components/blockchain/AnchorButton.tsx', 'Anchor button component'),
        ('interfaces/components/blockchain/VerificationBadge.tsx', 'Verification badge'),
        ('interfaces/components/blockchain/BlockchainStatusCard.tsx', 'Status card'),
        ('interfaces/components/blockchain/AnalysisCard.tsx', 'Analysis card'),
        ('interfaces/components/blockchain/index.ts', 'Components index'),
        ('interfaces/pages/dashboard/BlockchainPage.tsx', 'Blockchain page'),
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        full_path = os.path.join(frontend_path, file_path)
        exists = os.path.exists(full_path)
        print_test(f"{description}", exists, f"Missing: {file_path}" if not exists else "")
        if not exists:
            all_exist = False
    
    return all_exist

def test_frontend_build():
    """Verify frontend builds successfully"""
    print_section("Frontend Build Verification")
    
    dist_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
    
    if os.path.exists(dist_path):
        print_test("Frontend dist directory exists", True)
        
        # Check for build artifacts
        index_html = os.path.join(dist_path, 'index.html')
        assets_dir = os.path.join(dist_path, 'assets')
        
        print_test("index.html exists", os.path.exists(index_html))
        print_test("assets directory exists", os.path.exists(assets_dir))
        
        return os.path.exists(index_html)
    else:
        print_test("Frontend dist directory exists", False, "Run 'npm run build' in frontend/")
        return False

def run_all_tests():
    """Run all Phase 6 tests"""
    print(f"\n{Colors.BOLD}Phase 6 - Frontend Admin UI Tests{Colors.RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Frontend Files": test_frontend_files_exist(),
        "Frontend Build": test_frontend_build(),
        "Backend Connectivity": test_backend_connectivity(),
        "Blockchain Status (Public)": test_blockchain_status_endpoint(),
        "Analyses (Unauthenticated)": test_analyses_endpoint_unauthenticated(),
    }
    
    # Only run authenticated test if backend is up
    if results["Backend Connectivity"]:
        results["Analyses (Authenticated)"] = test_analyses_endpoint_authenticated()
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ Phase 6 Frontend Admin UI - All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed. Check the output above.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())