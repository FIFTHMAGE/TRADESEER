#!/usr/bin/env python3
"""
Final test of USDC purchase functionality with proper database setup
"""

import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_proper_test_data():
    """Set up test data with proper relationships"""
    print("🔧 Setting up proper test data...")
    
    try:
        db_file = 'tradeseer_bot.db'
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Clean up any existing test data
        test_chat_id = 12345
        cursor.execute('DELETE FROM connected_wallets WHERE chat_id = ?', (test_chat_id,))
        cursor.execute('DELETE FROM users WHERE chat_id = ?', (test_chat_id,))
        
        # Create test user first
        cursor.execute('''
            INSERT INTO users 
            (chat_id, username, first_name, last_name, registration_date, last_activity, is_active, user_type) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
        ''', (test_chat_id, 'testuser', 'Test', 'User', 1, 'regular'))
        
        # Get the user_id that was created
        user_id = cursor.lastrowid
        print(f"✅ Created user with ID: {user_id}")
        
        # Create test wallet with correct user_id (using a valid checksum address)
        test_wallet = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        
        cursor.execute('''
            INSERT INTO connected_wallets 
            (user_id, chat_id, wallet_address, wallet_name, is_active, date_connected) 
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, test_chat_id, test_wallet, 'Test Wallet', 1))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Test data setup complete")
        print(f"   - User ID: {user_id}")
        print(f"   - Chat ID: {test_chat_id}")
        print(f"   - Wallet: {test_wallet}")
        
        return test_chat_id, user_id, test_wallet
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def test_usdc_purchase_flow():
    """Test the complete USDC purchase flow"""
    print("\n🔍 Testing Complete USDC Purchase Flow:")
    
    try:
        from bot import get_user_by_chat_id, get_user_wallets, handle_buy_usdc
        
        test_chat_id, test_user_id, test_wallet = setup_proper_test_data()
        
        if not test_chat_id:
            print("❌ Cannot proceed without test data")
            return
        
        # Test 1: User retrieval
        print(f"\n📋 Test 1: User retrieval for chat_id: {test_chat_id}")
        user = get_user_by_chat_id(test_chat_id)
        if user:
            print(f"✅ User found: ID={user['user_id']}, Chat={user['chat_id']}")
            print(f"   Username: {user['username']}, Name: {user['first_name']} {user['last_name']}")
        else:
            print("❌ User not found")
            return
        
        # Test 2: Wallet retrieval
        print(f"\n📋 Test 2: Wallet retrieval for chat_id: {test_chat_id}")
        wallets = get_user_wallets(test_chat_id)
        if wallets:
            print(f"✅ Wallets found: {len(wallets)} wallets")
            for i, wallet in enumerate(wallets):
                print(f"   {i+1}. {wallet[0]} ({wallet[1]}) - Active: {wallet[2]}")
        else:
            print("❌ No wallets found")
            return
        
        # Test 3: USDC purchase with specific amount
        print(f"\n📋 Test 3: USDC purchase with amount: $100")
        try:
            result = handle_buy_usdc(test_chat_id, "100")
            print(f"✅ USDC purchase function executed successfully")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"❌ USDC purchase failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: USDC purchase without amount (should show menu)
        print(f"\n📋 Test 4: USDC purchase without amount (menu)")
        try:
            result = handle_buy_usdc(test_chat_id)
            print(f"✅ USDC purchase menu function executed successfully")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"❌ USDC purchase menu failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ USDC purchase flow test failed: {e}")
        import traceback
        traceback.print_exc()

def test_callback_handling():
    """Test callback handling for USDC purchase amounts"""
    print("\n🔍 Testing Callback Handling:")
    
    try:
        from bot import handle_callback_query
        
        test_chat_id = 12345
        
        # Test different callback types
        callbacks_to_test = [
            "buy_usdc_menu",
            "buy_usdc_100",
            "buy_usdc_custom"
        ]
        
        for callback_data in callbacks_to_test:
            print(f"\nTesting callback: {callback_data}")
            
            # Create a proper mock callback query object as a dictionary
            mock_callback = {
                'data': callback_data,
                'message': {
                    'chat': {
                        'id': test_chat_id
                    }
                }
            }
            
            try:
                result = handle_callback_query(mock_callback)
                print(f"✅ Callback '{callback_data}' handled successfully")
            except Exception as e:
                print(f"❌ Callback '{callback_data}' failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                
    except Exception as e:
        print(f"❌ Callback handling test failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_data():
    """Clean up test data from database"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        db_file = 'tradeseer_bot.db'
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Remove test user and associated data
        test_chat_id = 12345
        
        cursor.execute('DELETE FROM connected_wallets WHERE chat_id = ?', (test_chat_id,))
        cursor.execute('DELETE FROM users WHERE chat_id = ?', (test_chat_id,))
        
        conn.commit()
        conn.close()
        
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    print("🚀 TradeSeer USDC Purchase Final Test")
    print("=" * 50)
    
    try:
        test_usdc_purchase_flow()
        test_callback_handling()
    finally:
        cleanup_test_data()
    
    print("\n🏁 Final test completed!")
