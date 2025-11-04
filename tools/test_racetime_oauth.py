#!/usr/bin/env python3
"""
Test script to verify racetime.gg OAuth2 credentials.

This script tests the OAuth2 client_credentials flow to help debug
authentication issues with racetime bots.

Usage:
    cd /path/to/sahabot2
    poetry run python tools/test_racetime_oauth.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from config import settings


def test_oauth_credentials(
    racetime_url: str,
    category: str,
    client_id: str,
    client_secret: str
):
    """
    Test OAuth2 credentials against a racetime instance.
    
    Args:
        racetime_url: Base URL of racetime instance (e.g., http://localhost:8000)
        category: Category slug (e.g., 'test')
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
    """
    token_url = f"{racetime_url}/o/token"
    
    print(f"\n{'='*60}")
    print(f"Testing Racetime OAuth2 Credentials")
    print(f"{'='*60}")
    print(f"Racetime URL: {racetime_url}")
    print(f"Token endpoint: {token_url}")
    print(f"Category: {category}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret[:10]}..." if len(client_secret) > 10 else "***")
    print(f"{'='*60}\n")
    
    try:
        print("Sending OAuth2 token request...")
        resp = requests.post(token_url, {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
        })
        
        print(f"Response status: {resp.status_code}")
        
        if resp.status_code == 200:
            print("✅ SUCCESS! OAuth2 authentication successful.")
            data = resp.json()
            print(f"\nAccess token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"Expires in: {data.get('expires_in', 'N/A')} seconds")
            return True
        else:
            print(f"❌ FAILED! HTTP {resp.status_code}")
            print(f"\nResponse body:")
            print(resp.text)
            
            if resp.status_code == 401:
                print("\n⚠️  Authentication failed (401 Unauthorized)")
                print("\nPossible causes:")
                print("1. OAuth2 application doesn't exist in the racetime instance")
                print("2. Client ID or Client Secret is incorrect")
                print("3. OAuth2 application is not configured for 'client_credentials' grant type")
                print("\nHow to fix:")
                print(f"1. Access your racetime instance: {racetime_url}")
                print("2. Go to the admin panel (usually /admin)")
                print("3. Create or verify an OAuth2 application with:")
                print("   - Client type: Confidential")
                print("   - Authorization grant type: Client credentials")
                print(f"   - Category: {category}")
                print("4. Copy the Client ID and Client Secret")
                print("5. Update the bot configuration in SahaBot2")
            
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: Could not connect to {racetime_url}")
        print(f"Error: {e}")
        print("\nIs your racetime instance running?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    # Test with configured settings
    print("\nTesting with current configuration from .env:")
    
    racetime_url = settings.RACETIME_URL
    
    # You can manually set these values to test specific credentials
    # or fetch them from the database
    category = input("\nEnter category slug (e.g., 'test'): ").strip()
    client_id = input("Enter client ID: ").strip()
    client_secret = input("Enter client secret: ").strip()
    
    if not all([category, client_id, client_secret]):
        print("❌ All fields are required!")
        return
    
    success = test_oauth_credentials(
        racetime_url=racetime_url,
        category=category,
        client_id=client_id,
        client_secret=client_secret
    )
    
    if success:
        print("\n✅ Credentials are valid! You can use these in SahaBot2.")
    else:
        print("\n❌ Credentials are not valid. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
