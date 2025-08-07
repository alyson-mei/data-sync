#!/usr/bin/env python3
"""
Data Sync System - Test Suite

Comprehensive test suite for the data sync system.
Tests basic functionality, CLI operations, and git integration.

Usage:
    python test_sync.py
"""

import os
import tempfile
import shutil
import time
from pathlib import Path
import yaml
from sync_manager import SyncManager


def create_test_environment():
    """
    Create a test environment with temporary folders and configuration.
    
    Returns:
        tuple: (test_dir, config_path, local_folder)
    """
    # Create temporary directories
    test_dir = tempfile.mkdtemp(prefix="data_sync_test_")
    local_folder = os.path.join(test_dir, "local_folder")
    os.makedirs(local_folder, exist_ok=True)
    
    # Create test config
    test_config = {
        'sync_pairs': [
            {
                'name': 'test_sync',
                'local_folder': local_folder,
                'github_repo': 'testuser/test-repo',
                'github_token': '${TEST_GITHUB_TOKEN}',
                'autocommit_time': 10,  # Short for testing
                'branch': 'main',
                'commit_message_template': 'Test sync: {timestamp}',
                'ignore_patterns': ['*.tmp']
            }
        ],
        'global': {
            'sync_interval': 30,
            'max_retries': 3,
            'retry_delay': 5,
            'log_level': 'DEBUG',
            'log_file': 'test_sync.log'
        }
    }
    
    config_path = os.path.join(test_dir, "test_config.yaml")
    with open(config_path, 'w') as f:
        yaml.dump(test_config, f)
    
    return test_dir, config_path, local_folder


def test_basic_functionality():
    """
    Test basic functionality without actual GitHub operations.
    
    Returns:
        bool: True if test passes, False otherwise
    """
    print("🧪 Testing Data Sync System")
    print("=" * 50)
    
    # Create test environment
    test_dir, config_path, local_folder = create_test_environment()
    
    try:
        # Set a dummy token for testing
        os.environ['TEST_GITHUB_TOKEN'] = 'dummy_token_for_testing'
        
        # Create test file
        test_file = os.path.join(local_folder, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content\n")
        
        print(f"✅ Created test environment in: {test_dir}")
        print(f"✅ Created test file: {test_file}")
        
        # Test config loading
        try:
            manager = SyncManager(config_path)
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"❌ Configuration loading failed: {e}")
            return False
        
        # Test sync pair initialization
        try:
            manager.initialize_sync_pairs()
            print("✅ Sync pairs initialized successfully")
        except Exception as e:
            print(f"❌ Sync pair initialization failed: {e}")
            return False
        
        # Test git repository initialization
        git_folder = os.path.join(local_folder, '.git')
        if os.path.exists(git_folder):
            print("✅ Git repository initialized")
        else:
            print("❌ Git repository not initialized")
            return False
        
        print("\n🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test environment: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)


def test_cli_functionality():
    """
    Test CLI functionality.
    
    Returns:
        bool: True if test passes, False otherwise
    """
    print("\n🔧 Testing CLI Functionality")
    print("=" * 50)
    
    # Test config creation
    test_config = {
        'sync_pairs': [],
        'global': {
            'sync_interval': 60,
            'log_level': 'INFO',
            'log_file': 'sync.log'
        }
    }
    
    config_path = "test_cli_config.yaml"
    
    try:
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        print("✅ Test config created")
        
        # Test CLI list command
        import subprocess
        result = subprocess.run(['python', 'cli.py', 'list', '--config', config_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CLI list command works")
        else:
            print(f"❌ CLI list command failed: {result.stderr}")
        
        # Cleanup
        os.remove(config_path)
        print("✅ Test config cleaned up")
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False
    
    return True


def main():
    """
    Run all tests and display results.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("🚀 Data Sync System Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    basic_test_passed = test_basic_functionality()
    
    # Test CLI functionality
    cli_test_passed = test_cli_functionality()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"Basic functionality: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"CLI functionality: {'✅ PASSED' if cli_test_passed else '❌ FAILED'}")
    
    if basic_test_passed and cli_test_passed:
        print("\n🎉 All tests passed! The sync system is ready to use.")
        print("\nNext steps:")
        print("1. Set up your GitHub tokens in .env file")
        print("2. Configure your sync pairs in config.yaml")
        print("3. Run: python cli.py start")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return basic_test_passed and cli_test_passed


if __name__ == "__main__":
    main()
