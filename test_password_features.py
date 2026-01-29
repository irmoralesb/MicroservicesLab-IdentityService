"""
Manual Testing Script for Password Management Features

This script provides examples for testing the new password management features.
Replace the placeholders with actual values from your environment.

Prerequisites:
1. Start the service: uvicorn main:app --reload
2. Have an admin account with token
3. Have a test user account
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1/auth"
ADMIN_TOKEN = "your_admin_token_here"
USER_TOKEN = "your_user_token_here"

# Headers
admin_headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

user_headers = {
    "Authorization": f"Bearer {USER_TOKEN}",
    "Content-Type": "application/json"
}


def test_create_user_with_strong_password():
    """Test 1: Create user with strong password"""
    print("\n=== Test 1: Create User with Strong Password ===")
    
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "middle_name": "",
        "email": "testuser@example.com",
        "password": "SecureP@ss123"
    }
    
    response = requests.post(BASE_URL, headers=admin_headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_create_user_with_weak_password():
    """Test 2: Create user with weak password (should fail)"""
    print("\n=== Test 2: Create User with Weak Password ===")
    
    weak_passwords = [
        ("password", "Missing uppercase, digit, special char"),
        ("Pass123", "Missing special character"),
        ("P@ss", "Too short"),
        ("Password123", "Missing special character"),
        ("PASSWORD123!", "Missing lowercase"),
    ]
    
    for weak_pass, reason in weak_passwords:
        print(f"\nTrying: '{weak_pass}' - {reason}")
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "",
            "email": f"test_{weak_pass}@example.com",
            "password": weak_pass
        }
        
        response = requests.post(BASE_URL, headers=admin_headers, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 201:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")


def test_account_lockout():
    """Test 3: Account lockout after 3 failed attempts"""
    print("\n=== Test 3: Account Lockout Mechanism ===")
    
    test_email = "lockout.test@example.com"
    
    # First, create a user
    print("Creating test user...")
    payload = {
        "first_name": "Lockout",
        "last_name": "Test",
        "middle_name": "",
        "email": test_email,
        "password": "CorrectP@ss123"
    }
    requests.post(BASE_URL, headers=admin_headers, json=payload)
    
    # Try 3 failed login attempts
    for attempt in range(1, 4):
        print(f"\nAttempt {attempt}: Wrong password")
        login_data = {
            "username": test_email,
            "password": "WrongPassword123!"
        }
        response = requests.post(
            f"{BASE_URL}/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    
    # Try with correct password (should be locked)
    print("\nAttempt 4: Correct password (should be locked)")
    login_data = {
        "username": test_email,
        "password": "CorrectP@ss123"
    }
    response = requests.post(
        f"{BASE_URL}/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_change_password():
    """Test 4: User changes their own password"""
    print("\n=== Test 4: Change Password ===")
    
    payload = {
        "current_password": "OldP@ssword123",
        "new_password": "NewP@ssword456"
    }
    
    response = requests.post(
        f"{BASE_URL}/change-password",
        headers=user_headers,
        json=payload
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_unlock_account():
    """Test 5: Admin unlocks a locked account"""
    print("\n=== Test 5: Admin Unlock Account ===")
    
    # Replace with actual locked user ID
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    
    payload = {
        "user_id": user_id
    }
    
    response = requests.post(
        f"{BASE_URL}/unlock-account",
        headers=admin_headers,
        json=payload
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_password_validation_edge_cases():
    """Test 6: Password validation edge cases"""
    print("\n=== Test 6: Password Validation Edge Cases ===")
    
    test_cases = [
        ("P@ss1", "Too short (5 chars)"),
        ("P@ssw0rd", "Exactly 8 chars - should work"),
        ("P@ssw0rd" * 15, "Too long (>100 chars)"),
        ("Passw0rd!", "Valid - all requirements met"),
        ("   P@ss1   ", "Whitespace padding"),
    ]
    
    for password, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Length: {len(password)}")
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "middle_name": "",
            "email": f"test_{hash(password)}@example.com",
            "password": password
        }
        
        response = requests.post(BASE_URL, headers=admin_headers, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 201:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Password Management Testing Script")
    print("=" * 60)
    print("\nNOTE: Update ADMIN_TOKEN and USER_TOKEN before running!")
    print("Ensure the service is running on http://localhost:8000")
    
    # Uncomment the tests you want to run
    # test_create_user_with_strong_password()
    # test_create_user_with_weak_password()
    # test_account_lockout()
    # test_change_password()
    # test_unlock_account()
    # test_password_validation_edge_cases()
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    # Example: Get admin token first
    print("To get admin token, login as admin:")
    print('curl -X POST "http://localhost:8000/api/v1/auth/token" \\')
    print('  -H "Content-Type: application/x-www-form-urlencoded" \\')
    print('  -d "username=admin@example.com&password=YourAdminPassword"')
    print("\nThen update the ADMIN_TOKEN variable in this script.\n")
    
    # Uncomment to run tests
    # main()
