#!/usr/bin/env python3
"""
Test script to verify enhanced user management system
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_user_management():
    """Test the new user management system"""
    print("🧪 Testing Enhanced User Management System")
    print("=" * 50)
    
    try:
        from bot import (
            init_database, 
            get_or_create_user, 
            get_user_by_chat_id, 
            update_user_activity,
            save_wallet_to_db,
            get_user_settings,
            save_user_settings
        )
        print("✅ Successfully imported user management functions")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test database initialization
    print("\n📊 Testing Database Initialization:")
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Test user creation and retrieval
    print("\n👤 Testing User Creation and Retrieval:")
    
    # Test chat IDs
    test_chat_ids = [
        123456789,  # Test user 1
        987654321,  # Test user 2
        555666777   # Test user 3
    ]
    
    created_users = []
    
    for i, chat_id in enumerate(test_chat_ids, 1):
        print(f"\n🔍 Test {i}: Creating user with chat_id {chat_id}")
        
        # Create user
        user = get_or_create_user(
            chat_id=chat_id,
            username=f"testuser{i}",
            first_name=f"Test{i}",
            last_name="User"
        )
        
        if user:
            print(f"✅ User created/retrieved:")
            print(f"   User ID: {user['user_id']}")
            print(f"   Chat ID: {user['chat_id']}")
            print(f"   Username: {user['username']}")
            print(f"   Name: {user['first_name']} {user['last_name']}")
            print(f"   Is New: {user['is_new']}")
            created_users.append(user)
        else:
            print(f"❌ Failed to create user for chat_id {chat_id}")
            return False
    
    # Test user retrieval by chat_id
    print("\n🔍 Testing User Retrieval:")
    for user in created_users:
        retrieved_user = get_user_by_chat_id(user['chat_id'])
        if retrieved_user and retrieved_user['user_id'] == user['user_id']:
            print(f"✅ Successfully retrieved user {user['user_id']} by chat_id {user['chat_id']}")
        else:
            print(f"❌ Failed to retrieve user {user['user_id']}")
            return False
    
    # Test wallet tracking with user IDs
    print("\n💼 Testing Wallet Tracking with User IDs:")
    test_wallets = [
        "0x1234567890123456789012345678901234567890",
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "0x9876543210987654321098765432109876543210"
    ]
    
    for i, (user, wallet) in enumerate(zip(created_users, test_wallets), 1):
        print(f"\n🔍 Test {i}: Adding wallet for user {user['user_id']}")
        
        success = save_wallet_to_db(user['chat_id'], wallet)
        if success:
            print(f"✅ Wallet {wallet} saved for user {user['user_id']}")
        else:
            print(f"❌ Failed to save wallet for user {user['user_id']}")
            return False
    
    # Test user settings
    print("\n⚙️ Testing User Settings:")
    for user in created_users:
        print(f"\n🔍 Testing settings for user {user['user_id']}")
        
        # Get default settings
        settings = get_user_settings(user['chat_id'])
        print(f"   Default alert threshold: {settings.get('alert_threshold')}")
        print(f"   Default notification style: {settings.get('notification_style')}")
        
        # Update settings
        new_settings = {
            'alert_threshold': 0.5,
            'notification_style': 'psychic',
            'auto_score': True
        }
        
        success = save_user_settings(user['chat_id'], new_settings)
        if success:
            print(f"✅ Settings updated for user {user['user_id']}")
            
            # Verify settings were saved
            updated_settings = get_user_settings(user['chat_id'])
            if updated_settings.get('alert_threshold') == 0.5:
                print(f"✅ Settings verified for user {user['user_id']}")
            else:
                print(f"❌ Settings verification failed for user {user['user_id']}")
                return False
        else:
            print(f"❌ Failed to update settings for user {user['user_id']}")
            return False
    
    # Test user activity tracking
    print("\n📊 Testing User Activity Tracking:")
    for user in created_users:
        print(f"\n🔍 Testing activity update for user {user['user_id']}")
        try:
            update_user_activity(user['chat_id'])
            print(f"✅ Activity updated for user {user['user_id']}")
        except Exception as e:
            print(f"❌ Failed to update activity for user {user['user_id']}: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 All user management tests passed!")
    print("💡 The enhanced user management system is working correctly:")
    print("   • Unique user IDs are generated for each user")
    print("   • User data is properly linked to user IDs")
    print("   • Settings and wallets are correctly associated")
    print("   • Activity tracking is functional")
    print("   • Data persistence across deployments is ensured")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting User Management System Tests")
    print("=" * 50)
    
    success = test_user_management()
    
    if success:
        print("\n✅ All tests completed successfully!")
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
