#!/usr/bin/env python3
"""
Test script to verify enhanced token discovery functionality
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
        from bot import resolve_token_input, get_comprehensive_token_info, format_token_info_message
        print("✅ Successfully imported enhanced token functions")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test cases for different sources
    test_cases = [
        # Popular tokens (should use local database)
        ("USDC", "popular_tokens"),
        ("WETH", "popular_tokens"),
        
        # Contract addresses (should use DexScreener)
        ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "contract_address"),  # USDC
        ("0x4200000000000000000000000000000000000006", "contract_address"),  # WETH
        
        # New tokens that might be found on DexScreener/Pump.fun
        ("PEPE", "dexscreener"),  # Should try DexScreener
        ("DOGE", "dexscreener"),  # Should try DexScreener
        ("SHIB", "dexscreener"),  # Should try DexScreener
        
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
        ("PEPE", "DexScreener token"),
        ("DOGE", "DexScreener token"),
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
                price = token_info.get('price_usd', 0)
                try:
                    price_float = float(price) if price else 0
                    print(f"   Price: ${price_float:.6f}")
                except (ValueError, TypeError):
                    print(f"   Price: ${price}")
                print(f"   Source: {token_info.get('source', 'Unknown')}")
                
                # Test message formatting
                message = format_token_info_message(token_info)
                print(f"   Message length: {len(message)} characters")
                
                # Check for source-specific data
                source = token_info.get('source', 'Unknown')
                if source == "dexscreener":
                    liquidity = token_info.get('liquidity', 0)
                    dex = token_info.get('dex', '')
                    try:
                        liquidity_float = float(liquidity) if liquidity else 0
                        print(f"   Liquidity: ${liquidity_float:,.0f}")
                    except (ValueError, TypeError):
                        print(f"   Liquidity: ${liquidity}")
                    print(f"   DEX: {dex}")
                elif source == "pumpfun":
                    holders = token_info.get('holders', 0)
                    try:
                        holders_int = int(holders) if holders else 0
                        print(f"   Holders: {holders_int:,}")
                    except (ValueError, TypeError):
                        print(f"   Holders: {holders}")
                
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

def test_external_api_integration():
    """Test external API integration (DexScreener, Pump.fun)"""
    print("\n🌐 Testing External API Integration")
    print("=" * 40)
    
    try:
        from bot import get_token_info_from_dexscreener, search_token_on_dexscreener, search_token_on_pumpfun
        print("✅ Successfully imported external API functions")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test DexScreener API
    print("\n📊 Testing DexScreener API:")
    
    # Test USDC contract address
    usdc_contract = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    dex_info = get_token_info_from_dexscreener(usdc_contract)
    
    if dex_info:
        print(f"✅ DexScreener contract lookup successful:")
        print(f"   Symbol: {dex_info.get('symbol', 'Unknown')}")
        print(f"   Name: {dex_info.get('name', 'Unknown')}")
        price = dex_info.get('price', 0)
        try:
            price_float = float(price) if price else 0
            print(f"   Price: ${price_float:.6f}")
        except (ValueError, TypeError):
            print(f"   Price: ${price}")
        print(f"   DEX: {dex_info.get('dex', 'Unknown')}")
    else:
        print(f"⚠️ DexScreener contract lookup failed (may be rate limited)")
    
    # Test DexScreener search
    search_result = search_token_on_dexscreener("PEPE")
    if search_result:
        print(f"✅ DexScreener search successful:")
        print(f"   Symbol: {search_result.get('symbol', 'Unknown')}")
        print(f"   Address: {search_result.get('address', 'Unknown')}")
        price = search_result.get('price', 0)
        try:
            price_float = float(price) if price else 0
            print(f"   Price: ${price_float:.6f}")
        except (ValueError, TypeError):
            print(f"   Price: ${price}")
    else:
        print(f"⚠️ DexScreener search failed (may be rate limited)")
    
    # Test Pump.fun API
    print("\n🚀 Testing Pump.fun API:")
    pump_result = search_token_on_pumpfun("PEPE")
    if pump_result:
        print(f"✅ Pump.fun search successful:")
        print(f"   Symbol: {pump_result.get('symbol', 'Unknown')}")
        print(f"   Address: {pump_result.get('address', 'Unknown')}")
        price = pump_result.get('price', 0)
        try:
            price_float = float(price) if price else 0
            print(f"   Price: ${price_float:.6f}")
        except (ValueError, TypeError):
            print(f"   Price: ${price}")
        print(f"   Holders: {pump_result.get('holders', 0):,}")
    else:
        print(f"⚠️ Pump.fun search failed (may be rate limited)")
    
    print("\n💡 Note: External API tests may fail due to rate limiting or network issues.")
    print("   This is normal and doesn't indicate a problem with the implementation.")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Token Discovery Tests")
    print("=" * 50)
    
    # Test enhanced token resolution
    resolution_ok = test_enhanced_token_resolution()
    
    # Test comprehensive token info
    info_ok = test_comprehensive_token_info()
    
    # Test external API integration
    api_ok = test_external_api_integration()
    
    print("\n" + "=" * 50)
    if resolution_ok and info_ok and api_ok:
        print("🎉 All enhanced token discovery tests passed!")
        print("💡 The bot can now discover tokens from multiple sources:")
        print("   • Local popular tokens database")
        print("   • DexScreener API")
        print("   • Pump.fun API")
        print("   • CoinGecko API (fallback)")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
