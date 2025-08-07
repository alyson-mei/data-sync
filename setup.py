#!/usr/bin/env python3
"""
Data Sync System - Setup Script

Automated setup script for the data sync system.
Installs dependencies, creates configuration files, and runs tests.

Usage:
    python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """
    Check if Python version is compatible.
    
    Returns:
        bool: True if compatible, False otherwise
    """
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """
    Install required dependencies.
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("📦 Installing dependencies...")
    
    try:
        # Check if pip is available
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip not found. Please install pip first.")
        return False
    
    try:
        # Install dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_env_file():
    """
    Create .env file if it doesn't exist.
    
    Returns:
        bool: True if successful, False otherwise
    """
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file...")
    
    env_content = """# GitHub Personal Access Tokens
# Create tokens at: https://github.com/settings/tokens
# Required permissions: repo (Full control of private repositories)

GITHUB_TOKEN_1=your_first_github_token_here
GITHUB_TOKEN_2=your_second_github_token_here

# Add more tokens as needed for different sync pairs
# GITHUB_TOKEN_3=your_third_github_token_here
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your GitHub tokens")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def check_git():
    """
    Check if git is installed.
    
    Returns:
        bool: True if git is available, False otherwise
    """
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        print("✅ Git is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git is not installed. Please install git first.")
        return False


def run_tests():
    """
    Run the test suite.
    
    Returns:
        bool: True if tests pass, False otherwise
    """
    print("🧪 Running tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_sync.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests passed")
            return True
        else:
            print(f"❌ Tests failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your GitHub tokens")
    print("2. Configure your sync pairs in config.yaml")
    print("3. Test the system: python test_sync.py")
    print("4. Start the sync system: python cli.py start")
    print("\n📖 For more information, see README.md")


def main():
    """
    Main setup function.
    
    Performs all setup steps in sequence and handles errors gracefully.
    
    Returns:
        bool: True if setup succeeds, False otherwise
    """
    print("🚀 Data Sync System Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check git
    if not check_git():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    # Run tests
    if not run_tests():
        print("⚠️  Tests failed, but setup can continue")
    
    # Show next steps
    show_next_steps()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
