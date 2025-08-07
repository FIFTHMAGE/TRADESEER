#!/usr/bin/env python3
"""
Test script to verify token resolution functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_token_resolution():
    """Test the token resolution functionality"""
    print("🧪 TradeSeer Token Resolution Test Suite")
    print("=" * 50)
    
    # Import the resolve_token_input function
    try:
        from bot import resolve_token_input, POPULAR_TOKENS
        print("✅ Successfully imported token resolution functions")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test cases
    test_cases = [
        # (input, expected_symbol, expected_source)
        ("USDC", "USDC", "popular_tokens"),
        ("usdc", "USDC", "popular_tokens"),
        ("USDT", "USDT", "popular_tokens"),
        ("WETH", "WETH", "popular_tokens"),
        ("pepe", "PEPE", "popular_tokens"),
        ("doge", "DOGE", "popular_tokens"),
        ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "USDC", "contract_address"),
        ("0x4200000000000000000000000000000000000006", "WETH", "contract_address"),
        ("invalid_token", None, "not_found"),
        ("", None, "not_found"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (token_input, expected_symbol, expected_source) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total}: {token_input}")
        
        try:
            contract_address, token_symbol, source = resolve_token_input(token_input)
            
            if expected_symbol is None:
                # Expected to fail
                if contract_address is None:
                    print(f"✅ Correctly failed to resolve: {token_input}")
                    passed += 1
                else:
                    print(f"❌ Should have failed but got: {contract_address}")
            else:
                # Expected to succeed
                if contract_address and token_symbol == expected_symbol:
                    print(f"✅ Successfully resolved: {token_input} -> {token_symbol} ({source})")
                    print(f"   Contract: {contract_address}")
                    passed += 1
                else:
                    print(f"❌ Failed to resolve correctly:")
                    print(f"   Expected: {expected_symbol}")
                    print(f"   Got: {token_symbol}")
                    print(f"   Address: {contract_address}")
                    print(f"   Source: {source}")
        
        except Exception as e:
            print(f"❌ Error during resolution: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Token resolution is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

def test_popular_tokens():
    """Test the popular tokens database"""
    print("\n🔍 Testing Popular Tokens Database")
    print("=" * 30)
    
    try:
        from bot import POPULAR_TOKENS
        print(f"✅ Found {len(POPULAR_TOKENS)} popular tokens")
        
        # Test a few key tokens
        key_tokens = ["usdc", "usdt", "weth", "link", "uni", "aave"]
        for token in key_tokens:
            if token in POPULAR_TOKENS:
                print(f"✅ {token.upper()}: {POPULAR_TOKENS[token]}")
            else:
                print(f"❌ Missing: {token.upper()}")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import POPULAR_TOKENS: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Token Resolution Tests")
    print("=" * 50)
    
    # Test popular tokens database
    tokens_ok = test_popular_tokens()
    
    # Test token resolution
    resolution_ok = test_token_resolution()
    
    print("\n" + "=" * 50)
    if tokens_ok and resolution_ok:
        print("🎉 All token resolution tests passed!")
        print("💡 The bot can now handle both CA and ticker symbols.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 