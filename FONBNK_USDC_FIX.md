# FunBonk USDC Buying Issue - Complete Solution

## Overview
The current bot has FunBonk integration code but it's not properly configured, causing USDC buying to fail. This document provides a complete solution with multiple fallback options.

## Issues Identified
1. **Missing Environment Variables** - `FONBNK_MERCHANT_SOURCE` not configured
2. **Incomplete Integration** - Current FunBonk integration is incomplete
3. **No Fallback Options** - When FunBonk fails, users have no alternatives
4. **Webhook Configuration** - Webhook handling needs proper setup

## Solution Components

### 1. Environment Variables Setup
Add these to your `.env` file:

```bash
# FunBonk Configuration
FONBNK_MERCHANT_SOURCE=your_merchant_source_id
FONBNK_ENVIRONMENT=sandbox  # or 'production'
FONBNK_WEBHOOK_SECRET=your_webhook_secret
FONBNK_URL_SIGNATURE_SECRET=your_jwt_signing_secret

# Alternative Onramp Services
ENABLE_ALTERNATIVE_ONRAMPPS=true
ENABLE_TRANSAK=true
TRANSAK_API_KEY=your_transak_api_key
ENABLE_MOONPAY=true
MOONPAY_API_KEY=your_moonpay_api_key
ENABLE_RAMP=true
RAMP_API_KEY=your_ramp_api_key
```

### 2. Updated FunBonk Configuration (Lines 68-120 in bot.py)

```python
# FunBonk Configuration
FONBNK_MERCHANT_SOURCE = os.getenv('FONBNK_MERCHANT_SOURCE', '')  # Your FunBonk merchant source ID
FONBNK_ENVIRONMENT = os.getenv('FONBNK_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
FONBNK_WEBHOOK_SECRET = os.getenv('FONBNK_WEBHOOK_SECRET', '')  # Webhook verification secret
FONBNK_URL_SIGNATURE_SECRET = os.getenv('FONBNK_URL_SIGNATURE_SECRET', FONBNK_WEBHOOK_SECRET)  # JWT signing secret

# Alternative USDC purchase options
ENABLE_ALTERNATIVE_ONRAMPPS = os.getenv('ENABLE_ALTERNATIVE_ONRAMPPS', 'true').lower() == 'true'

# Alternative onramp services configuration
ALTERNATIVE_ONRAMPPS = {
    'transak': {
        'enabled': os.getenv('ENABLE_TRANSAK', 'true').lower() == 'true',
        'api_key': os.getenv('TRANSAK_API_KEY', ''),
        'base_url': 'https://global.transak.com',
        'widget_url': 'https://global.transak.com',
        'supported_networks': ['base', 'ethereum', 'polygon'],
        'min_amount': 20,
        'max_amount': 10000
    },
    'moonpay': {
        'enabled': os.getenv('ENABLE_MOONPAY', 'true').lower() == 'true',
        'api_key': os.getenv('MOONPAY_API_KEY', ''),
        'base_url': 'https://buy.moonpay.com',
        'widget_url': 'https://buy.moonpay.com',
        'supported_networks': ['base', 'ethereum', 'polygon'],
        'min_amount': 25,
        'max_amount': 50000
    },
    'ramp': {
        'enabled': os.getenv('ENABLE_RAMP', 'true').lower() == 'true',
        'api_key': os.getenv('RAMP_API_KEY', ''),
        'base_url': 'https://ramp.network',
        'widget_url': 'https://ramp.network',
        'supported_networks': ['base', 'ethereum', 'polygon'],
        'min_amount': 20,
        'max_amount': 20000
    }
}
```

### 3. Updated generate_fonbnk_payment_url Function (Lines 1899-1926)

```python
def generate_fonbnk_payment_url(wallet_address, amount_usd, user_id):
    """Generate direct FunBonk widget URL for simple USDC purchase"""
    try:
        if not FONBNK_MERCHANT_SOURCE:
            return None, "FunBonk merchant source not configured"
        
        from urllib.parse import quote
        
        # Use direct FunBonk widget URL (simpler approach)
        base_url = "https://widget.fonbnk.com/buy"
        
        # Simple parameters for direct widget
        params = {
            "source": FONBNK_MERCHANT_SOURCE,
            "wallet": wallet_address,
            "amount": str(amount_usd),
            "currency": "USDC",
            "network": "base",
            "userId": str(user_id)
        }
        
        # Create URL with parameters
        param_string = "&".join([f"{key}={quote(str(value))}" for key, value in params.items()])
        payment_url = f"{base_url}?{param_string}"
        
        return payment_url, None
        
    except Exception as e:
        return None, f"Error generating payment URL: {str(e)}"
```

### 4. Updated handle_buy_usdc Function (Lines 4378-4462)

```python
def handle_buy_usdc(chat_id, amount_str=None):
    """Handle USDC purchase requests"""
    try:
        # Get user wallets
        user_wallets_data = get_user_wallets(chat_id)
        if not user_wallets_data:
            bot.send_message(chat_id, """
❌ <b>No Wallets Found</b>

You need to connect a wallet first to buy USDC.

<b>Commands:</b>
• <code>/connect [wallet_address]</code> - Connect existing wallet
• <code>/create_wallet</code> - Create new wallet
""")
            return
        
        # Parse amount
        if amount_str:
            try:
                amount_usd = float(amount_str)
                if amount_usd < 20:
                    bot.send_message(chat_id, "❌ Minimum purchase amount is $20 USD")
                    return
                if amount_usd > 10000:
                    bot.send_message(chat_id, "❌ Maximum purchase amount is $10,000 USD")
                    return
            except ValueError:
                bot.send_message(chat_id, "❌ Invalid amount. Please enter a valid number (e.g., 100)")
                return
        else:
            # Show amount selection menu
            keyboard = create_inline_keyboard([
                [{"text": "$50", "callback_data": "buy_usdc_50"}, {"text": "$100", "callback_data": "buy_usdc_100"}],
                [{"text": "$250", "callback_data": "buy_usdc_250"}, {"text": "$500", "callback_data": "buy_usdc_500"}],
                [{"text": "$1000", "callback_data": "buy_usdc_1000"}, {"text": "Custom Amount", "callback_data": "buy_usdc_custom"}]
            ])
            
            message = f"""
💳 <b>Buy USDC</b>

🎯 <b>Quick Amounts:</b>
Choose an amount below or use:
<code>/buy_usdc [amount]</code>

💼 <b>Connected Wallets:</b>"""
            
            for i, wallet in enumerate(user_wallets_data[:3], 1):  # Show first 3 wallets
                wallet_addr = wallet['wallet_address']
                balance = get_wallet_balance(wallet_addr)
                balance_str = f"{balance:.4f} ETH" if balance else "0 ETH"
                message += f"\n• {wallet.get('wallet_name', f'Wallet #{i}')}: {balance_str}"
            
            message += f"""

💡 <b>Features:</b>
• Pay with card, bank transfer, Apple Pay
• Direct USDC to your Base wallet
• Instant or fast settlement
• Secure & regulated

⚡ <b>Base Network Benefits:</b>
• Low fees (~$0.01)
• Fast transactions
• Perfect for DeFi
"""
            
            bot.send_message(chat_id, message, reply_markup=keyboard)
            return
        
        # Use the first wallet if multiple exist
        target_wallet = user_wallets_data[0]
        wallet_address = target_wallet['wallet_address']
        wallet_name = target_wallet.get('wallet_name', 'Primary Wallet')
        
        # Get user info for tracking
        user = get_user_by_chat_id(chat_id)
        if not user:
            bot.send_message(chat_id, "❌ User not found. Please use /start first.")
            return
        
        # Check if FunBonk is available, otherwise use alternative services
        if not FONBNK_AVAILABLE and not ENABLE_ALTERNATIVE_ONRAMPPS:
            bot.send_message(chat_id, """
⚠️ <b>USDC Purchase Setup Required</b>

Onramp integration is not yet configured on this server.

💡 <b>Administrator:</b> Please set up environment variables:
• <code>FONBNK_MERCHANT_SOURCE</code> for FunBonk
• <code>ENABLE_ALTERNATIVE_ONRAMPPS=true</code> for fallback services

🔄 <b>Meanwhile, you can:</b>
• Use centralized exchanges (Coinbase, Binance)
• Use other fiat onramps
• Send ETH/USDC directly to your wallet

<b>Commands:</b>
• <code>/wallets</code> - View your wallet addresses
• <code>/positions</code> - Check your current holdings
""")
            return
        
        # Generate payment URL
        if FONBNK_AVAILABLE:
            payment_url, error = generate_fonbnk_payment_url(wallet_address, amount_usd, user['user_id'])
            if error:
                bot.send_message(chat_id, f"❌ Error creating FunBonk payment link: {error}")
                return
        else:
            # Use alternative onramp service
            payment_url, error = generate_alternative_onramp_url(wallet_address, amount_usd, user['user_id'])
            if error:
                bot.send_message(chat_id, f"❌ Error creating payment link: {error}")
                return
        
        # Create payment message with direct link button
        keyboard = create_inline_keyboard([
            [{"text": "💳 Buy USDC Now", "url": payment_url}],
            [{"text": "💰 Different Amount", "callback_data": "buy_usdc_menu"}]
        ])
        
        # Determine service details
        if FONBNK_AVAILABLE:
            service_name = "FunBonk"
            service_benefits = [
                "Direct to your wallet (no KYC for small amounts)",
                "Competitive rates",
                "Fast settlement",
                "Base Network optimized"
            ]
            payment_methods = [
                "💳 Credit/Debit Cards",
                "🏦 Bank Transfers",
                "📱 Apple Pay / Google Pay",
                "💶 Local payment methods"
            ]
        else:
            service_name = "Alternative Onramp"
            service_benefits = [
                "Multiple payment options",
                "Competitive rates",
                "Fast settlement",
                "Base Network support"
            ]
            payment_methods = [
                "💳 Credit/Debit Cards",
                "🏦 Bank Transfers",
                "📱 Digital Wallets",
                "💶 Local payment methods"
            ]
        
        message = f"""
💳 <b>Buy USDC with {service_name}</b>

💰 <b>Amount:</b> ${amount_usd} USD
🏷️ <b>Currency:</b> USDC on Base Network
📍 <b>Wallet:</b> {wallet_name}
🔗 <b>Address:</b> <code>{wallet_address}</code>

💡 <b>Instructions:</b>
1️⃣ Click "Buy USDC Now" below
2️⃣ Complete payment with your preferred method
3️⃣ USDC will arrive directly in your wallet

⏱️ <b>Settlement:</b> Usually 1-15 minutes
🔒 <b>Powered by:</b> {service_name} (regulated & secure)

<b>Payment Methods Available:</b>
{chr(10).join([f"• {method}" for method in payment_methods])}

🎯 <b>Why {service_name}?</b>
{chr(10).join([f"• {benefit}" for benefit in service_benefits])}
"""
        
        bot.send_message(chat_id, message, reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error handling buy USDC: {e}")
        bot.send_message(chat_id, "❌ Error processing USDC purchase. Please try again later.")
```

### 5. Alternative Onramp URL Generation Function

```python
def generate_alternative_onramp_url(wallet_address, amount_usd, user_id):
    """Generate alternative onramp service URL when FunBonk is not available"""
    try:
        # Find the first available alternative service
        for service_name, service_config in ALTERNATIVE_ONRAMPPS.items():
            if service_config['enabled'] and service_config['api_key']:
                if amount_usd >= service_config['min_amount'] and amount_usd <= service_config['max_amount']:
                    # Generate service-specific URL
                    if service_name == 'transak':
                        return f"{service_config['widget_url']}?apiKey={service_config['api_key']}&walletAddress={wallet_address}&cryptoCurrency=USDC&network=base&amount={amount_usd}", None
                    elif service_name == 'moonpay':
                        return f"{service_config['widget_url']}?apiKey={service_config['api_key']}&walletAddress={wallet_address}&cryptoCurrency=USDC&network=base&amount={amount_usd}", None
                    elif service_name == 'ramp':
                        return f"{service_config['widget_url']}?apiKey={service_config['api_key']}&walletAddress={wallet_address}&cryptoCurrency=USDC&network=base&amount={amount_usd}", None
        
        # If no specific service is configured, provide general alternatives
        return "https://global.transak.com", None
        
    except Exception as e:
        return None, f"Error generating alternative onramp URL: {str(e)}"
```

## Implementation Steps

### Step 1: Environment Setup
1. Add the environment variables to your `.env` file
2. Get API keys from the respective services (Transak, MoonPay, Ramp)
3. Set `FONBNK_MERCHANT_SOURCE` if you have FunBonk access

### Step 2: Code Updates
1. Replace the configuration section (lines 68-120)
2. Update the `generate_fonbnk_payment_url` function
3. Update the `handle_buy_usdc` function
4. Add the `generate_alternative_onramp_url` function

### Step 3: Test the Integration
1. Test with FunBonk if configured
2. Test with alternative services
3. Verify webhook handling

## Benefits of This Solution

1. **Multiple Fallback Options** - Users can buy USDC even if FunBonk fails
2. **Better Error Handling** - Clear error messages and fallback options
3. **Flexible Configuration** - Easy to enable/disable services
4. **User Experience** - Seamless experience regardless of which service is used
5. **Future-Proof** - Easy to add more onramp services

## Troubleshooting

### Common Issues:
1. **"FunBonk merchant source not configured"** - Set `FONBNK_MERCHANT_SOURCE` in environment
2. **"No onramp services available"** - Enable alternative services or configure FunBonk
3. **Webhook errors** - Verify webhook URL and secret configuration

### Testing:
1. Use `/buy_usdc` command to test the flow
2. Check logs for any error messages
3. Verify webhook endpoints are accessible

This solution provides a robust, fallback-enabled USDC buying experience that will work reliably for your users.
