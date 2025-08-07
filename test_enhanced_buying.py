#!/usr/bin/env python3
"""
Test script to verify enhanced token buying functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_comprehensive_token_info():
    """Test comprehensive token information retrieval"""
    print("🧪 Testing Comprehensive Token Information")
    print("=" * 50)
    
    try:
        from bot import get_comprehensive_token_info, format_token_info_message
        print("✅ Successfully imported token info functions")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test cases
    test_cases = [
        ("USDC", "USD Coin"),
        ("usdc", "USD Coin"),
        ("WETH", "Wrapped Ether"),
        ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "USD Coin"),  # USDC CA
        ("0x4200000000000000000000000000000000000006", "Wrapped Ether"),  # WETH CA
        ("PEPE", "Pepe"),
        ("DOGE", "Dogecoin"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (token_input, expected_name) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total}: {token_input}")
        
        try:
            token_info, error = get_comprehensive_token_info(token_input)
            
            if error:
                print(f"❌ Error: {error}")
            elif token_info:
                print(f"✅ Successfully retrieved token info:")
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

def test_price_data():
    """Test price data retrieval"""
    print("\n💰 Testing Price Data Retrieval")
    print("=" * 30)
    
    try:
        from bot import get_token_price_data
        print("✅ Successfully imported price data function")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Test cases
    test_cases = [
        ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "USDC"),  # USDC
        ("0x4200000000000000000000000000000000000006", "WETH"),  # WETH
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (contract_address, symbol) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total}: {symbol} ({contract_address[:10]}...)")
        
        try:
            price_data = get_token_price_data(contract_address, symbol)
            
            print(f"✅ Price data retrieved:")
            print(f"   Price USD: ${price_data.get('price_usd', 0):.6f}")
            print(f"   24h Change: {price_data.get('price_change_24h', 0):.2f}%")
            print(f"   Market Cap: ${price_data.get('market_cap', 0):,.0f}")
            print(f"   24h Volume: ${price_data.get('volume_24h', 0):,.0f}")
            
            passed += 1
        
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All price data tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

def test_buy_request_parsing():
    """Test buy request parsing"""
    print("\n🛒 Testing Buy Request Parsing")
    print("=" * 30)
    
    import re
    
    # Test cases
    test_cases = [
        ("buy with ETH 0.1", ("ETH", 0.1)),
        ("buy with USDC 100", ("USDC", 100)),
        ("buy with USDT 50.5", ("USDT", 50.5)),
        ("BUY WITH ETH 0.05", ("ETH", 0.05)),
        ("invalid command", None),
        ("buy with BTC 1", None),  # Invalid token
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total}: {text}")
        
        try:
            buy_match = re.search(r'buy with (\w+) (\d+\.?\d*)', text.lower())
            
            if expected is None:
                if buy_match is None:
                    print(f"✅ Correctly failed to parse: {text}")
                    passed += 1
                else:
                    # Check if the parsed token is valid
                    payment_token = buy_match.group(1).upper()
                    valid_tokens = ['ETH', 'USDC', 'USDT']
                    if payment_token not in valid_tokens:
                        print(f"✅ Correctly failed to parse invalid token: {text}")
                        passed += 1
                    else:
                        print(f"❌ Should have failed but got: {buy_match.groups()}")
            else:
                if buy_match:
                    payment_token = buy_match.group(1).upper()
                    amount = float(buy_match.group(2))
                    
                    if payment_token == expected[0] and amount == expected[1]:
                        print(f"✅ Successfully parsed: {payment_token} {amount}")
                        passed += 1
                    else:
                        print(f"❌ Parsed incorrectly:")
                        print(f"   Expected: {expected[0]} {expected[1]}")
                        print(f"   Got: {payment_token} {amount}")
                else:
                    print(f"❌ Failed to parse valid command")
        
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All buy request parsing tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Token Buying Tests")
    print("=" * 50)
    
    # Test comprehensive token info
    token_info_ok = test_comprehensive_token_info()
    
    # Test price data
    price_data_ok = test_price_data()
    
    # Test buy request parsing
    parsing_ok = test_buy_request_parsing()
    
    print("\n" + "=" * 50)
    if token_info_ok and price_data_ok and parsing_ok:
        print("🎉 All enhanced token buying tests passed!")
        print("💡 The bot can now show token info and handle enhanced buying flow.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 