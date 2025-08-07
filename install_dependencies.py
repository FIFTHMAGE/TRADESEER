#!/usr/bin/env python3
"""
Installation script for TradeSeer Bot dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def check_package(package):
    """Check if a package is installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """Install missing dependencies"""
    print("🔧 TradeSeer Bot Dependency Installer")
    print("=" * 50)
    
    # Required packages for wallet creation
    required_packages = [
        "web3",
        "eth-account", 
        "cryptography",
        "Flask",
        "requests",
        "python-dotenv"
    ]
    
    print("🔍 Checking current installations...")
    
    missing_packages = []
    for package in required_packages:
        if check_package(package.replace("-", "_")):
            print(f"✅ {package} already installed")
        else:
            print(f"❌ {package} not found")
            missing_packages.append(package)
    
    if not missing_packages:
        print("\n🎉 All required packages are already installed!")
        return True
    
    print(f"\n📦 Installing {len(missing_packages)} missing packages...")
    
    success_count = 0
    for package in missing_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Installation Summary:")
    print(f"✅ Successfully installed: {success_count}/{len(missing_packages)} packages")
    
    if success_count == len(missing_packages):
        print("\n🎉 All dependencies installed successfully!")
        print("\n💡 Next steps:")
        print("1. Run: python test_wallet_creation.py")
        print("2. Start the bot: python bot.py")
        return True
    else:
        print(f"\n❌ {len(missing_packages) - success_count} packages failed to install")
        print("Please try installing them manually:")
        for package in missing_packages:
            print(f"   pip install {package}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 