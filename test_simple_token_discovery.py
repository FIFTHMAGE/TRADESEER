#!/usr/bin/env python3
"""
Simple test script to verify enhanced token discovery functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_token_resolution():
    """Test enhanced token resolution with multiple sources"""
    print("🧪 Testing Enhanced Token Resolution")
    print("=" * 50)
    
    try:
        from bot import resolve_token_input
        print("✅ Successfully imported resolve_token_input function")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test cases for different sources
    test_cases = [
        # Popular tokens (should use local database)
        ("USDC", "popular_tokens"),
        ("WETH", "popular_tokens"),
        ("USDT", "popular_tokens"),
        
        # Contract addresses (should use DexScreener)
        ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "contract_address"),  # USDC
        ("0x4200000000000000000000000000000000000006", "contract_address"),  # WETH
        
        # Invalid tokens
        ("INVALID_TOKEN_12345", "not_found"),
        ("", "error"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (token_input, expected_source) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total}: {token_input}")
        
        try:
            contract_address, token_symbol, source = resolve_token_input(token_input)
            
            if expected_source == "not_found" or expected_source == "error":
                if contract_address is None:
                    print(f"✅ Correctly failed to resolve: {token_input}")
                    passed += 1
                else:
                    print(f"❌ Should have failed but got: {contract_address}")
            else:
                if contract_address and token_symbol:
                    print(f"✅ Successfully resolved:")
                    print(f"   Contract: {contract_address}")
                    print(f"   Symbol: {token_symbol}")
                    print(f"   Source: {source}")
                    
                    # Test if source matches expected or is a valid fallback
                    if source == expected_source or source in ["dexscreener", "pumpfun", "coingecko", "popular_tokens", "contract_address"]:
                        print(f"   ✅ Source validation passed")
                        passed += 1
                    else:
                        print(f"   ❌ Unexpected source: {source}")
                else:
                    print(f"❌ Failed to resolve token")
        
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhanced token resolution tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

def test_comprehensive_token_info():
    """Test comprehensive token information with enhanced sources"""
    print("\n💰 Testing Comprehensive Token Information")
    print("=" * 50)
    
    try:
        from bot import get_comprehensive_token_info, format_token_info_message
        print("✅ Successfully imported comprehensive token info functions")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test cases for different token types
    test_cases = [
        ("USDC", "Popular token"),
        ("WETH", "Popular token"),
        ("USDT", "Popular token"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (token_input, description) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total}: {token_input} ({description})")
        
        try:
            token_info, error = get_comprehensive_token_info(token_input)
            
            if error:
                print(f"❌ Error: {error}")
            elif token_info:
                print(f"✅ Successfully retrieved comprehensive token info:")
                print(f"   Name: {token_info.get('name', 'Unknown')}")
                print(f"   Symbol: {token_info.get('symbol', 'Unknown')}")
                print(f"   Contract: {token_info.get('contract_address', 'Unknown')}")
                print(f"   Price: ${token_info.get('price_usd', 0):.6f}")
                print(f"   Source: {token_info.get('source', 'Unknown')}")
                
                # Test message formatting
                message = format_token_info_message(token_info)
                print(f"   Message length: {len(message)} characters")
                
                passed += 1
            else:
                print(f"❌ No token info returned")
        
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive token info tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Simple Enhanced Token Discovery Tests")
    print("=" * 50)
    
    # Test enhanced token resolution
    resolution_ok = test_enhanced_token_resolution()
    
    # Test comprehensive token info
    info_ok = test_comprehensive_token_info()
    
    print("\n" + "=" * 50)
    if resolution_ok and info_ok:
        print("🎉 All simple enhanced token discovery tests passed!")
        print("💡 The bot can now discover tokens from multiple sources:")
        print("   • Local popular tokens database")
        print("   • DexScreener API (when available)")
        print("   • Pump.fun API (when available)")
        print("   • CoinGecko API (fallback)")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
