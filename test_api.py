"""Simple API test script."""

import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_root():
    """Test root endpoint."""
    print("Testing root endpoint...")
    response = requests.get(BASE_URL)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_categories():
    """Test categories endpoint."""
    print("Testing categories endpoint...")
    try:
        response = requests.get(f"{API_URL}/categories")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} categories")
            if data:
                print("First category:", data[0])
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_users():
    """Test users endpoint."""
    print("Testing users endpoint...")
    try:
        response = requests.get(f"{API_URL}/users")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} users")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_cameras():
    """Test cameras endpoint."""
    print("Testing cameras endpoint...")
    try:
        response = requests.get(f"{API_URL}/cameras")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} cameras")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_discussions():
    """Test discussions endpoint."""
    print("Testing discussions endpoint...")
    try:
        response = requests.get(f"{API_URL}/discussions")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} discussions")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("RetroLens API Test")
    print("=" * 50)
    print()
    
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    test_health()
    test_root()
    test_categories()
    test_users()
    test_cameras()
    test_discussions()
    
    print("=" * 50)
    print("Test complete!")
    print("Visit http://localhost:8000/api/v1/docs for interactive documentation")
    print("=" * 50)
