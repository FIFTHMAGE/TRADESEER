#!/usr/bin/env python3
"""
Comprehensive test of bot integration for USDC purchases
"""

import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_test_database():
    """Set up a test database with a test user and wallet"""
    print("🔧 Setting up test database...")
    
    try:
        # Connect to the bot's database
        db_file = 'tradeseer_bot.db'
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create test user
        test_chat_id = 12345
        test_user_id = 1
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, chat_id, username, first_name, last_name, is_active) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_user_id, test_chat_id, 'testuser', 'Test', 'User', 1))
        
        # Create test wallet
        test_wallet = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        
        cursor.execute('''
            INSERT OR REPLACE INTO connected_wallets 
            (user_id, chat_id, wallet_address, wallet_name, is_active) 
            VALUES (?, ?, ?, ?, ?)
        ''', (test_user_id, test_chat_id, test_wallet, 'Test Wallet', 1))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Test database setup complete")
        print(f"   - User ID: {test_user_id}")
        print(f"   - Chat ID: {test_chat_id}")
        print(f"   - Wallet: {test_wallet}")
        
        return test_chat_id, test_user_id, test_wallet
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return None, None, None

def test_bot_functions_with_data():
    """Test bot functions with actual database data"""
    print("\n🔍 Testing Bot Functions with Database Data:")
    
    try:
        from bot import get_user_by_chat_id, get_user_wallets, handle_buy_usdc
        
        test_chat_id, test_user_id, test_wallet = setup_test_database()
        
        if not test_chat_id:
            print("❌ Cannot proceed without test data")
            return
        
        # Test user retrieval
        print(f"\nTesting user retrieval for chat_id: {test_chat_id}")
        user = get_user_by_chat_id(test_chat_id)
        if user:
            print(f"✅ User found: ID={user['user_id']}, Chat={user['chat_id']}")
        else:
            print("❌ User not found")
            return
        
        # Test wallet retrieval
        print(f"\nTesting wallet retrieval for chat_id: {test_chat_id}")
        wallets = get_user_wallets(test_chat_id)
        if wallets:
            print(f"✅ Wallets found: {len(wallets)} wallets")
            for i, wallet in enumerate(wallets):
                print(f"   {i+1}. {wallet[0]} ({wallet[1]}) - Active: {wallet[2]}")
        else:
            print("❌ No wallets found")
            return
        
        # Test USDC purchase with amount
        print(f"\nTesting USDC purchase with amount: $100")
        try:
            result = handle_buy_usdc(test_chat_id, "100")
            print(f"✅ USDC purchase function executed: {result}")
        except Exception as e:
            print(f"❌ USDC purchase failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test USDC purchase without amount (should show menu)
        print(f"\nTesting USDC purchase without amount (menu)")
        try:
            result = handle_buy_usdc(test_chat_id)
            print(f"✅ USDC purchase menu function executed: {result}")
        except Exception as e:
            print(f"❌ USDC purchase menu failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Bot functions test failed: {e}")
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
    print("🚀 TradeSeer Bot Integration Test")
    print("=" * 50)
    
    try:
        test_bot_functions_with_data()
        test_callback_handling()
    finally:
        cleanup_test_data()
    
    print("\n🏁 Integration test completed!")
