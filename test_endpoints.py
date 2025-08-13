# test_endpoints.py
# Test script to verify candidate endpoints

import requests
import json

BASE_URL = "http://127.0.0.1:8005"

def test_endpoints():
    """Test all candidate endpoints"""
    
    print("🧪 Testing Candidate Endpoints...")
    print("=" * 50)
    
    # Test 1: Get candidates (should require auth)
    print("\n1. Testing GET /candidate (requires auth)...")
    try:
        response = requests.get(f"{BASE_URL}/candidate")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Correctly requires authentication")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Add candidate (should require auth)
    print("\n2. Testing POST /candidate (requires auth)...")
    try:
        response = requests.post(f"{BASE_URL}/candidate", json={"name": "Test Candidate"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Correctly requires authentication")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Revalidation endpoints (should require auth)
    print("\n3. Testing revalidation endpoints (requires auth)...")
    reverify_endpoints = [
        "/candidate/1/reverify/identity",
        "/candidate/1/reverify/employment", 
        "/candidate/1/reverify/aml",
        "/candidate/1/reverify/bankAccount",
        "/candidate/1/reverify/court"
    ]
    
    for endpoint in reverify_endpoints:
        try:
            response = requests.post(f"{BASE_URL}{endpoint}")
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 401:
                print("   ✓ Correctly requires authentication")
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    # Test 4: Bulk upload endpoint (should require auth)
    print("\n4. Testing POST /candidate/upload (requires auth)...")
    try:
        response = requests.post(f"{BASE_URL}/candidate/upload")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Correctly requires authentication")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Check API documentation
    print("\n5. Testing API documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ API documentation is accessible")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Endpoint testing completed!")
    print("\n📝 Next steps:")
    print("1. Get a valid JWT token by logging in")
    print("2. Use the token in Authorization header: 'Bearer <token>'")
    print("3. Test the endpoints with proper authentication")

if __name__ == "__main__":
    test_endpoints() 