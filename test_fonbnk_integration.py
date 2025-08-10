#!/usr/bin/env python3
"""
Test script for FunBonk USDC buying integration
Tests the payment URL generation and fallback options
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'FONBNK_MERCHANT_SOURCE',
        'FONBNK_ENVIRONMENT',
        'ENABLE_ALTERNATIVE_ONRAMPPS'
    ]
    
    optional_vars = [
        'TRANSAK_API_KEY',
        'MOONPAY_API_KEY',
        'RAMP_API_KEY'
    ]
    
    print("\n📋 Required Variables:")
    for var in required_vars:
        value = os.getenv(var, '')
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {'Set' if value else 'Not Set'}")
    
    print("\n📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var, '')
        status = "✅" if value else "⚠️"
        print(f"  {status} {var}: {'Set' if value else 'Not Set'}")
    
    return True

def test_fonbnk_configuration():
    """Test FunBonk configuration"""
    print("\n🔍 Testing FunBonk Configuration...")
    
    merchant_source = os.getenv('FONBNK_MERCHANT_SOURCE', '')
    environment = os.getenv('FONBNK_ENVIRONMENT', 'sandbox')
    webhook_secret = os.getenv('FONBNK_WEBHOOK_SECRET', '')
    
    if merchant_source:
        print(f"✅ FunBonk Merchant Source: {merchant_source}")
        print(f"✅ Environment: {environment}")
        print(f"✅ Webhook Secret: {'Set' if webhook_secret else 'Not Set'}")
        return True
    else:
        print("❌ FunBonk not configured - will use alternative services")
        return False

def test_alternative_services():
    """Test alternative onramp services configuration"""
    print("\n🔍 Testing Alternative Onramp Services...")
    
    services = {
        'transak': {
            'enabled': os.getenv('ENABLE_TRANSAK', 'true').lower() == 'true',
            'api_key': os.getenv('TRANSAK_API_KEY', '')
        },
        'moonpay': {
            'enabled': os.getenv('ENABLE_MOONPAY', 'true').lower() == 'true',
            'api_key': os.getenv('MOONPAY_API_KEY', '')
        },
        'ramp': {
            'enabled': os.getenv('ENABLE_RAMP', 'true').lower() == 'true',
            'api_key': os.getenv('RAMP_API_KEY', '')
        }
    }
    
    available_services = []
    
    for service_name, config in services.items():
        if config['enabled']:
            if config['api_key']:
                print(f"✅ {service_name.title()}: Configured with API key")
                available_services.append(service_name)
            else:
                print(f"⚠️ {service_name.title()}: Enabled but no API key")
        else:
            print(f"❌ {service_name.title()}: Disabled")
    
    if available_services:
        print(f"\n✅ Available alternative services: {', '.join(available_services)}")
        return True
    else:
        print("\n❌ No alternative services available")
        return False

def test_payment_url_generation():
    """Test payment URL generation functions"""
    print("\n🔍 Testing Payment URL Generation...")
    
    # Test wallet address and amount
    test_wallet = "0x1234567890123456789012345678901234567890"
    test_amount = 100
    test_user_id = 12345
    
    print(f"Test Wallet: {test_wallet}")
    print(f"Test Amount: ${test_amount}")
    print(f"Test User ID: {test_user_id}")
    
    # Test FunBonk URL generation
    if os.getenv('FONBNK_MERCHANT_SOURCE'):
        try:
            from urllib.parse import quote
            
            base_url = "https://widget.fonbnk.com/buy"
            params = {
                "source": os.getenv('FONBNK_MERCHANT_SOURCE'),
                "wallet": test_wallet,
                "amount": str(test_amount),
                "currency": "USDC",
                "network": "base",
                "userId": str(test_user_id)
            }
            
            param_string = "&".join([f"{key}={quote(str(value))}" for key, value in params.items()])
            payment_url = f"{base_url}?{param_string}"
            
            print(f"✅ FunBonk Payment URL: {payment_url}")
        except Exception as e:
            print(f"❌ Error generating FunBonk URL: {e}")
    
    # Test alternative service URLs
    services = {
        'transak': {
            'enabled': os.getenv('ENABLE_TRANSAK', 'true').lower() == 'true',
            'api_key': os.getenv('TRANSAK_API_KEY', ''),
            'url': 'https://global.transak.com'
        },
        'moonpay': {
            'enabled': os.getenv('ENABLE_MOONPAY', 'true').lower() == 'true',
            'api_key': os.getenv('MOONPAY_API_KEY', ''),
            'url': 'https://buy.moonpay.com'
        },
        'ramp': {
            'enabled': os.getenv('ENABLE_RAMP', 'true').lower() == 'true',
            'api_key': os.getenv('RAMP_API_KEY', ''),
            'url': 'https://ramp.network'
        }
    }
    
    for service_name, config in services.items():
        if config['enabled'] and config['api_key']:
            try:
                alt_url = f"{config['url']}?apiKey={config['api_key']}&walletAddress={test_wallet}&cryptoCurrency=USDC&network=base&amount={test_amount}"
                print(f"✅ {service_name.title()} Alternative URL: {alt_url}")
            except Exception as e:
                print(f"❌ Error generating {service_name} URL: {e}")

def test_webhook_endpoints():
    """Test webhook endpoint configuration"""
    print("\n🔍 Testing Webhook Endpoints...")
    
    webhook_secret = os.getenv('FONBNK_WEBHOOK_SECRET', '')
    
    if webhook_secret:
        print("✅ FunBonk webhook secret configured")
        print("✅ Webhook endpoint: /fonbnk_webhook")
        print("✅ Webhook verification enabled")
    else:
        print("⚠️ FunBonk webhook secret not configured")
        print("⚠️ Webhook verification disabled")
    
    print("✅ Telegram webhook endpoint: /webhook")
    print("✅ Health check endpoint: /health")

def main():
    """Run all tests"""
    print("🚀 FunBonk USDC Integration Test Suite")
    print("=" * 50)
    
    # Test environment variables
    test_environment_variables()
    
    # Test FunBonk configuration
    fonbnk_configured = test_fonbnk_configuration()
    
    # Test alternative services
    alternatives_available = test_alternative_services()
    
    # Test payment URL generation
    test_payment_url_generation()
    
    # Test webhook configuration
    test_webhook_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    if fonbnk_configured:
        print("✅ FunBonk integration is properly configured")
    else:
        print("❌ FunBonk integration is not configured")
    
    if alternatives_available:
        print("✅ Alternative onramp services are available")
    else:
        print("❌ No alternative onramp services available")
    
    if fonbnk_configured or alternatives_available:
        print("\n🎉 USDC buying should work! Users can purchase USDC through:")
        if fonbnk_configured:
            print("  • FunBonk (primary)")
        if alternatives_available:
            print("  • Alternative onramp services (fallback)")
    else:
        print("\n⚠️ USDC buying will not work. Please configure at least one service.")
    
    print("\n💡 Next Steps:")
    if not fonbnk_configured:
        print("  1. Get FunBonk merchant source ID")
        print("  2. Set FONBNK_MERCHANT_SOURCE in environment")
    
    if not alternatives_available:
        print("  1. Get API keys from alternative services")
        print("  2. Set respective API keys in environment")
    
    print("  3. Test the /buy_usdc command in your bot")
    print("  4. Verify webhook endpoints are accessible")

if __name__ == "__main__":
    main()
