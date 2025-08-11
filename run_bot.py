#!/usr/bin/env python3
"""
Simple script to run the TradeSeer bot
"""

import sys
import os

# Set encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Import and run the bot
try:
    from bot import app
    print("✅ Bot imported successfully")
    print("🚀 Starting Flask server...")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except Exception as e:
    print(f"❌ Error starting bot: {e}")
    import traceback
    traceback.print_exc()
