# 🔐 Wallet Creation Troubleshooting Guide

## Issue: "Create wallet is not working"

If you're experiencing issues with wallet creation in TradeSeer Bot, this guide will help you resolve them.

## 🔍 Quick Diagnosis

### 1. Check Dependencies
The wallet creation feature requires specific Python packages. Run this test:

```bash
python test_wallet_creation.py
```

If the test fails, you'll see which dependencies are missing.

### 2. Install Missing Dependencies

#### Automatic Installation
```bash
python install_dependencies.py
```

#### Manual Installation
```bash
pip install web3 eth-account cryptography Flask requests python-dotenv
```

## 🚨 Common Issues & Solutions

### Issue 1: "Account creation not available - missing eth_account dependency"

**Solution:**
```bash
pip install eth-account
```

### Issue 2: "Encryption not available - missing cryptography dependency"

**Solution:**
```bash
pip install cryptography
```

### Issue 3: "Web3 not available"

**Solution:**
```bash
pip install web3
```

### Issue 4: Database Permission Errors

**Solution:**
- Ensure the bot has write permissions to the current directory
- Check if `tradeseer_bot.db` file is not locked by another process

### Issue 5: Password Requirements

**Requirements:**
- Minimum 8 characters
- Can contain letters, numbers, and special characters

**Example valid password:**
```
MySecurePassword123!
```

## 🧪 Testing Your Setup

### Step 1: Run Dependency Test
```bash
python test_wallet_creation.py
```

Expected output:
```
🧪 TradeSeer Wallet Creation Test Suite
==================================================
🔍 Testing dependencies...
✅ Web3 available
✅ eth_account available
✅ cryptography available

🔐 Testing wallet creation...
✅ Account created successfully
📍 Address: 0x...
🔑 Private key length: 64 characters
✅ Private key encrypted successfully
🔒 Encrypted key length: ... bytes
✅ Private key decrypted successfully

🗄️ Testing database...
✅ Database tables created successfully
✅ Test database cleaned up

==================================================
🎉 All tests passed! Wallet creation should work properly.
```

### Step 2: Test in Bot
1. Start the bot: `python bot.py`
2. Send message: `create wallet name:TestWallet password:MyPassword123!`
3. You should receive a success message with wallet address

## 🔧 Manual Installation Steps

If automatic installation fails, install packages manually:

```bash
# Core dependencies
pip install Flask==2.3.3
pip install requests==2.31.0
pip install python-dotenv==1.0.0

# Web3 and blockchain
pip install web3==6.11.3
pip install eth-account==0.9.0
pip install eth-utils==2.2.0

# Cryptography
pip install cryptography==41.0.7
```

## 🌐 Environment Setup

### Required Environment Variables
Create a `.env` file with:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ETHERSCAN_API_KEY=your_etherscan_api_key_here
WEBHOOK_URL=your_webhook_url_here
```

### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📱 Using Wallet Creation

### Command Format
```
create wallet name:WalletName password:YourPassword123!
```

### Example
```
create wallet name:TradingWallet password:SecurePass123!
```

### What Happens
1. ✅ Creates new Ethereum wallet
2. ✅ Encrypts private key with your password
3. ✅ Stores encrypted key securely in database
4. ✅ Returns wallet address for funding

### Security Features
- 🔒 Private keys encrypted with PBKDF2
- 🔑 Password-based encryption
- 🗄️ Secure database storage
- 🚫 No plaintext private key storage

## 🆘 Still Having Issues?

### Check Bot Logs
Look for these messages when starting the bot:
```
✅ Account creation available
✅ Cryptography features available
✅ Wallet features available
```

If you see ❌ instead of ✅, the dependencies are missing.

### Common Error Messages

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'eth_account'` | `pip install eth-account` |
| `ModuleNotFoundError: No module named 'cryptography'` | `pip install cryptography` |
| `ModuleNotFoundError: No module named 'web3'` | `pip install web3` |
| `Password must be at least 8 characters long` | Use longer password |
| `Database locked` | Restart bot, check file permissions |

### Get Help
1. Run the test script: `python test_wallet_creation.py`
2. Check the output for specific error messages
3. Install missing dependencies as indicated
4. Restart the bot and try again

## ✅ Success Indicators

When wallet creation is working properly, you should see:

1. **Bot startup messages:**
   ```
   ✅ Account creation available
   ✅ Cryptography features available  
   ✅ Wallet features available
   ```

2. **Successful wallet creation:**
   ```
   ✅ Wallet Created Successfully!
   
   🏷️ Name: MyWallet
   📍 Address: 0x...
   🔗 Network: Base Network
   ```

3. **Database tables created:**
   ```
   ✅ Database initialized with wallet connection support
   ```

---

**Need more help?** Check the main README.md file or run the test scripts to diagnose specific issues. 