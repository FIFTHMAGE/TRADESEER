#!/usr/bin/env python3
"""
Test script to verify wallet creation functionality
"""

import sys
import os

def test_dependencies():
    """Test if all required dependencies are available"""
    print("🔍 Testing dependencies...")
    
    # Test Web3
    try:
        from web3 import Web3
        print("✅ Web3 available")
    except ImportError as e:
        print(f"❌ Web3 not available: {e}")
        return False
    
    # Test Account
    try:
        from eth_account import Account
        print("✅ eth_account available")
    except ImportError as e:
        print(f"❌ eth_account not available: {e}")
        return False
    
    # Test Cryptography
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        print("✅ cryptography available")
    except ImportError as e:
        print(f"❌ cryptography not available: {e}")
        return False
    
    return True

def test_wallet_creation():
    """Test wallet creation functionality"""
    print("\n🔐 Testing wallet creation...")
    
    try:
        from eth_account import Account
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        import os
        
        # Test account creation
        account = Account.create()
        private_key = account.key.hex()
        wallet_address = account.address
        
        print(f"✅ Account created successfully")
        print(f"📍 Address: {wallet_address}")
        print(f"🔑 Private key length: {len(private_key)} characters")
        
        # Test encryption
        password = "TestPassword123!"
        salt = os.urandom(16)
        
        # Generate encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Encrypt private key
        f = Fernet(key)
        encrypted_key = f.encrypt(private_key.encode())
        
        print(f"✅ Private key encrypted successfully")
        print(f"🔒 Encrypted key length: {len(encrypted_key)} bytes")
        
        # Test decryption
        decrypted_key = f.decrypt(encrypted_key)
        decrypted_private_key = decrypted_key.decode()
        
        if decrypted_private_key == private_key:
            print("✅ Private key decrypted successfully")
        else:
            print("❌ Private key decryption failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Wallet creation test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n🗄️ Testing database...")
    
    try:
        import sqlite3
        
        # Create test database
        test_db = 'test_wallet.db'
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connected_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                wallet_address TEXT NOT NULL,
                wallet_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                date_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, wallet_address)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                wallet_address TEXT NOT NULL,
                encrypted_private_key TEXT NOT NULL,
                salt TEXT NOT NULL,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, wallet_address)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Database tables created successfully")
        
        # Clean up test database
        os.remove(test_db)
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 TradeSeer Wallet Creation Test Suite")
    print("=" * 50)
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n❌ Dependencies test failed. Please install missing packages:")
        print("pip install web3 eth-account cryptography")
        return False
    
    # Test wallet creation
    wallet_ok = test_wallet_creation()
    
    # Test database
    db_ok = test_database()
    
    print("\n" + "=" * 50)
    if deps_ok and wallet_ok and db_ok:
        print("🎉 All tests passed! Wallet creation should work properly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 