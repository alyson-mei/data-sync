#!/usr/bin/env python3
"""
Data Sync System - Command Line Interface

Provides a command-line interface for managing the data sync system.
Supports setup, monitoring, testing, and status checking operations.

Usage:
    python cli.py setup <name> <local_folder> <github_repo> <token_env> [options]
    python cli.py list [--config <file>]
    python cli.py status [--config <file>]
    python cli.py start [--config <file>]
    python cli.py test <name> [--config <file>]
"""

import argparse
import sys
import os
from sync_manager import SyncManager
import yaml


def setup_command(args):
    """
    Setup a new sync pair.
    
    Creates or updates the configuration file with a new sync pair.
    """
    config_path = args.config or "config.yaml"
    
    # Load existing config or create new one
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {'sync_pairs': [], 'global': {}}
    
    # Create new sync pair
    new_pair = {
        'name': args.name,
        'local_folder': args.local_folder,
        'github_repo': args.github_repo,
        'github_token': f"${{{args.token_env}}}",
        'autocommit_time': args.autocommit_time,
        'branch': args.branch,
        'commit_message_template': args.commit_template,
        'ignore_patterns': args.ignore_patterns.split(',') if args.ignore_patterns else []
    }
    
    # Add to config
    config['sync_pairs'].append(new_pair)
    
    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Added sync pair '{args.name}' to {config_path}")
    print(f"   Local folder: {args.local_folder}")
    print(f"   GitHub repo: {args.github_repo}")
    print(f"   Token env var: {args.token_env}")
    print(f"   Autocommit time: {args.autocommit_time} seconds")


def list_command(args):
    """
    List all configured sync pairs.
    
    Displays all sync pairs with their configuration details.
    """
    config_path = args.config or "config.yaml"
    
    if not os.path.exists(config_path):
        print("❌ Configuration file not found")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("📋 Sync Pairs:")
    print("=" * 80)
    
    for pair in config.get('sync_pairs', []):
        print(f"Name: {pair['name']}")
        print(f"  Local folder: {pair['local_folder']}")
        print(f"  GitHub repo: {pair['github_repo']}")
        print(f"  Autocommit time: {pair.get('autocommit_time', 300)} seconds")
        print(f"  Branch: {pair.get('branch', 'main')}")
        print(f"  Ignore patterns: {', '.join(pair.get('ignore_patterns', []))}")
        print("-" * 40)


def status_command(args):
    """
    Show status of sync pairs.
    
    Displays the current status of all sync pairs including git initialization
    and last sync times.
    """
    try:
        manager = SyncManager(args.config or "config.yaml")
        manager.initialize_sync_pairs()
        
        print("📊 Sync Status:")
        print("=" * 80)
        
        for name, sync_pair in manager.sync_pairs.items():
            print(f"🔗 {name}:")
            print(f"  Local folder: {sync_pair.local_folder}")
            print(f"  GitHub repo: {sync_pair.github_repo}")
            print(f"  Git initialized: {'✅' if os.path.exists(os.path.join(sync_pair.local_folder, '.git')) else '❌'}")
            print(f"  Last sync: {sync_pair.last_sync_time}")
            print("-" * 40)
    
    except Exception as e:
        print(f"❌ Error: {e}")


def start_command(args):
    """
    Start the sync system.
    
    Initializes and starts the complete sync system with all configured pairs.
    """
    try:
        manager = SyncManager(args.config or "config.yaml")
        print("🚀 Starting data sync system...")
        print("Press Ctrl+C to stop")
        import asyncio
        asyncio.run(manager.start_sync())
    except KeyboardInterrupt:
        print("\n🛑 Sync system stopped")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_command(args):
    """
    Test a specific sync pair.
    
    Performs a test sync operation on the specified sync pair to verify
    git operations and connectivity.
    """
    try:
        manager = SyncManager(args.config or "config.yaml")
        manager.initialize_sync_pairs()
        
        if args.name not in manager.sync_pairs:
            print(f"❌ Sync pair '{args.name}' not found")
            return
        
        sync_pair = manager.sync_pairs[args.name]
        print(f"🧪 Testing sync pair: {args.name}")
        
        # Test git operations
        print("  Testing git pull...")
        sync_pair._pull_changes()
        
        print("  Testing change detection...")
        has_changes = sync_pair._has_changes()
        print(f"  Has changes: {'✅' if has_changes else '❌'}")
        
        if has_changes:
            print("  Testing commit and push...")
            sync_pair._commit_and_push()
        
        print("✅ Test completed")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """
    Main CLI entry point.
    
    Parses command line arguments and dispatches to appropriate command handlers.
    """
    parser = argparse.ArgumentParser(
        description="Data Sync System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py setup documents /home/user/docs username/repo GITHUB_TOKEN_1
  python cli.py list
  python cli.py status
  python cli.py start
  python cli.py test documents
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup a new sync pair')
    setup_parser.add_argument('name', help='Name of the sync pair')
    setup_parser.add_argument('local_folder', help='Local folder path')
    setup_parser.add_argument('github_repo', help='GitHub repository (username/repo)')
    setup_parser.add_argument('token_env', help='Environment variable name for GitHub token')
    setup_parser.add_argument('--autocommit-time', type=int, default=300, 
                             help='Autocommit time in seconds (default: 300)')
    setup_parser.add_argument('--branch', default='main', help='Git branch (default: main)')
    setup_parser.add_argument('--commit-template', default='Sync: {timestamp}', 
                             help='Commit message template')
    setup_parser.add_argument('--ignore-patterns', help='Comma-separated ignore patterns')
    setup_parser.add_argument('--config', help='Configuration file path')
    setup_parser.set_defaults(func=setup_command)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all sync pairs')
    list_parser.add_argument('--config', help='Configuration file path')
    list_parser.set_defaults(func=list_command)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show sync status')
    status_parser.add_argument('--config', help='Configuration file path')
    status_parser.set_defaults(func=status_command)
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the sync system')
    start_parser.add_argument('--config', help='Configuration file path')
    start_parser.set_defaults(func=start_command)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a sync pair')
    test_parser.add_argument('name', help='Name of the sync pair to test')
    test_parser.add_argument('--config', help='Configuration file path')
    test_parser.set_defaults(func=test_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
