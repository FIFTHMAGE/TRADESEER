#!/usr/bin/env python3
"""
Test script to verify bot dependency detection
"""

# Import the dependency checking logic from bot.py
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_bot_dependencies():
    """Test the bot's dependency detection"""
    print("🔍 Testing Bot Dependency Detection")
    print("=" * 50)
    
    # Test Web3
    WEB3_AVAILABLE = False
    try:
        from web3 import Web3
        from eth_utils import to_checksum_address
        WEB3_AVAILABLE = True
        print("✅ Web3 available for full blockchain functionality")
    except ImportError as e:
        print(f"⚠️ Web3 not available - some features may be limited: {e}")

    # Test Account
    ACCOUNT_AVAILABLE = False
    try:
        from eth_account import Account
        ACCOUNT_AVAILABLE = True
        print("✅ Account creation available")
    except ImportError as e:
        print(f"❌ Account features not available: {e}")

    # Test Cryptography
    CRYPTO_AVAILABLE = False
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        CRYPTO_AVAILABLE = True
        print("✅ Cryptography features available")
    except ImportError as e:
        print(f"❌ Cryptography features not available: {e}")

    # Set wallet availability based on required components
    WALLET_AVAILABLE = False
    if ACCOUNT_AVAILABLE and CRYPTO_AVAILABLE:
        WALLET_AVAILABLE = True
        print("✅ Wallet features available")
    else:
        print("❌ Wallet features not available - missing required dependencies")
    
    print("\n" + "=" * 50)
    if WALLET_AVAILABLE:
        print("🎉 All wallet creation dependencies are available!")
        print("💡 The 'create wallet' feature should work properly now.")
        return True
    else:
        print("❌ Some dependencies are missing for wallet creation.")
        return False

if __name__ == "__main__":
    success = test_bot_dependencies()
    sys.exit(0 if success else 1) 