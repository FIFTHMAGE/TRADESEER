#!/usr/bin/env python3
"""
Fix invalid wallet addresses in the TradeSeer database
"""

import sqlite3
from web3 import Web3
import re

def is_valid_ethereum_address(address):
    """Check if an address is a valid Ethereum address"""
    if not address or not isinstance(address, str):
        return False
    
    # Check if it's a valid hex string
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False
    
    try:
        # Try to convert to checksum address
        checksum_address = Web3.to_checksum_address(address)
        return checksum_address == address
    except Exception:
        return False

def fix_database():
    """Fix invalid wallet addresses in the database"""
    conn = sqlite3.connect('tradeseer_bot.db')
    cursor = conn.cursor()
    
    print("🔧 Fixing invalid wallet addresses...")
    
    # Check connected_wallets table
    cursor.execute("SELECT id, wallet_address FROM connected_wallets")
    connected_wallets = cursor.fetchall()
    
    print(f"📊 Found {len(connected_wallets)} connected wallets")
    
    invalid_count = 0
    for wallet_id, address in connected_wallets:
        if not is_valid_ethereum_address(address):
            print(f"❌ Invalid address: {address}")
            invalid_count += 1
            
            # Remove invalid wallet
            cursor.execute("DELETE FROM connected_wallets WHERE id = ?", (wallet_id,))
            print(f"🗑️ Removed invalid wallet {wallet_id}")
    
    # Check tracked_wallets table if it exists
    try:
        cursor.execute("SELECT id, wallet_address FROM tracked_wallets")
        tracked_wallets = cursor.fetchall()
        
        print(f"📊 Found {len(tracked_wallets)} tracked wallets")
        
        for wallet_id, address in tracked_wallets:
            if not is_valid_ethereum_address(address):
                print(f"❌ Invalid tracked address: {address}")
                invalid_count += 1
                
                # Remove invalid tracked wallet
                cursor.execute("DELETE FROM tracked_wallets WHERE id = ?", (wallet_id,))
                print(f"🗑️ Removed invalid tracked wallet {wallet_id}")
    except sqlite3.OperationalError:
        print("ℹ️ tracked_wallets table doesn't exist")
    
    # Add some valid test addresses
    valid_addresses = [
        "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
        "0x8ba1f109551bD432803012645Hac136c772c3c7c",
        "0xE4B055A5869Dbc1480b1Dffb84679f2E4C6637dc"
    ]
    
    print("✅ Adding valid test addresses...")
    for i, address in enumerate(valid_addresses):
        if is_valid_ethereum_address(address):
            cursor.execute("""
                INSERT INTO connected_wallets (user_id, chat_id, wallet_address, wallet_name, is_active, date_connected)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (1, 123456789, address, f"TestWallet{i+1}", 1))
            print(f"✅ Added valid address: {address}")
        else:
            print(f"❌ Skipping invalid address: {address}")
    
    conn.commit()
    conn.close()
    
    print(f"🎉 Database cleanup complete! Removed {invalid_count} invalid addresses")

if __name__ == "__main__":
    fix_database()
