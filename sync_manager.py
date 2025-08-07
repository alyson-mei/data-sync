#!/usr/bin/env python3
"""
Data Sync System - Core Manager

A robust Python-based data synchronization system that automatically syncs local folders 
with GitHub repositories. Features real-time file monitoring, configurable sync intervals,
and conflict resolution with GitHub-first strategy.

Key Features:
- Real-time file system monitoring with debouncing
- Automatic git operations (pull, commit, push)
- Configurable sync intervals per repository
- GitHub-first conflict resolution
- Comprehensive logging with colored output
- Secure token management via environment variables

Author: Data Sync System
License: MIT
"""

import os
import yaml
import git
import time
import logging
import colorlog
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
import schedule
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

# Load environment variables from .env file
load_dotenv()


class SyncManager:
    """
    Main orchestrator for the data sync system.
    
    Manages multiple sync pairs, file watchers, and scheduled sync operations.
    Each sync pair represents a local folder that syncs with a GitHub repository.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the sync manager.
        
        Args:
            config_path (str): Path to the YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.setup_logging()
        self.sync_pairs = {}
        self.observers = []
        
    def _load_config(self) -> Dict:
        """
        Load and validate configuration from YAML file.
        
        Returns:
            Dict: Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid YAML
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_path} not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration: {e}")
    
    def setup_logging(self):
        """
        Setup colored console logging and file logging.
        
        Creates a dual logging system with colored console output for real-time
        monitoring and file logging for persistent records.
        """
        log_level = self.config.get('global', {}).get('log_level', 'INFO')
        log_file = self.config.get('global', {}).get('log_file', 'sync.log')
        
        # Create colored formatter for console
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        
        # Configure logger
        self.logger = logging.getLogger('DataSync')
        self.logger.setLevel(getattr(logging, log_level))
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def initialize_sync_pairs(self):
        """
        Initialize all sync pairs from configuration.
        
        Creates SyncPair instances for each configured folder-repo mapping
        and sets up git repositories.
        """
        for pair_config in self.config.get('sync_pairs', []):
            try:
                sync_pair = SyncPair(pair_config, self.logger)
                self.sync_pairs[pair_config['name']] = sync_pair
                self.logger.info(f"Initialized sync pair: {pair_config['name']}")
            except Exception as e:
                self.logger.error(f"Failed to initialize sync pair {pair_config['name']}: {e}")
    
    async def start_sync(self):
        """
        Start the complete synchronization system (async version).
        Initializes sync pairs, starts file watchers, and begins scheduled sync.
        Runs until interrupted.
        """
        self.logger.info("Starting data sync system (async)...")
        self.initialize_sync_pairs()

        # Start file watchers for each sync pair (still blocking, so run in thread)
        watcher_tasks = [
            asyncio.create_task(self._start_file_watcher_async(sync_pair))
            for sync_pair in self.sync_pairs.values()
        ]

        # Start scheduled sync
        scheduler_task = asyncio.create_task(self._start_scheduled_sync_async())

        try:
            await asyncio.gather(*watcher_tasks, scheduler_task)
        except asyncio.CancelledError:
            self.logger.info("Shutting down sync system...")

    async def _start_file_watcher_async(self, sync_pair):
        """
        Async file watcher using polling (watchdog is not async).
        """
        event_handler = SyncEventHandler(sync_pair, self.logger)
        observer = Observer()
        observer.schedule(event_handler, sync_pair.local_folder, recursive=True)
        observer.start()
        self.observers.append(observer)
        self.logger.info(f"Started file watcher for: {sync_pair.name}")
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            observer.stop()
            observer.join()

    async def _start_scheduled_sync_async(self):
        """
        Async scheduled synchronization at regular intervals.
        """
        sync_interval = self.config.get('global', {}).get('sync_interval', 60)
        while True:
            for name, sync_pair in self.sync_pairs.items():
                try:
                    await asyncio.to_thread(sync_pair.sync)
                except Exception as e:
                    self.logger.error(f"Error syncing {name}: {e}")
            await asyncio.sleep(sync_interval)
    
    def start_sync_old(self):
        """
        Start the complete synchronization system.
        
        Initializes sync pairs, starts file watchers, and begins scheduled sync.
        Runs indefinitely until interrupted.
        """
        self.logger.info("Starting data sync system...")
        self.initialize_sync_pairs()
        
        # Start file watchers for each sync pair
        for name, sync_pair in self.sync_pairs.items():
            self._start_file_watcher(sync_pair)
        
        # Start scheduled sync
        self._start_scheduled_sync()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down sync system...")
            self._stop_all_observers()
    
    def _start_file_watcher(self, sync_pair):
        """
        Start file system watcher for a sync pair.
        
        Args:
            sync_pair (SyncPair): The sync pair to monitor
        """
        event_handler = SyncEventHandler(sync_pair, self.logger)
        observer = Observer()
        observer.schedule(event_handler, sync_pair.local_folder, recursive=True)
        observer.start()
        self.observers.append(observer)
        self.logger.info(f"Started file watcher for: {sync_pair.name}")
    
    def _start_scheduled_sync(self):
        """
        Start scheduled synchronization at regular intervals.
        
        Uses the schedule library to run sync operations at configured intervals.
        """
        sync_interval = self.config.get('global', {}).get('sync_interval', 60)
        
        def sync_all():
            """Sync all pairs and handle errors gracefully."""
            for name, sync_pair in self.sync_pairs.items():
                try:
                    sync_pair.sync()
                except Exception as e:
                    self.logger.error(f"Error syncing {name}: {e}")
        
        schedule.every(sync_interval).seconds.do(sync_all)
        
        def run_scheduler():
            """Run the scheduler in a separate thread."""
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info(f"Started scheduled sync every {sync_interval} seconds")
    
    def _stop_all_observers(self):
        """Stop all file system observers gracefully."""
        for observer in self.observers:
            observer.stop()
        for observer in self.observers:
            observer.join()


class SyncPair:
    """
    Represents a single folder-to-repository sync pair.
    
    Handles git operations, conflict resolution, and change detection for one
    local folder that syncs with one GitHub repository.
    """
    
    def __init__(self, config: Dict, logger: logging.Logger):
        """
        Initialize a sync pair.
        
        Args:
            config (Dict): Configuration dictionary for this sync pair
            logger (logging.Logger): Logger instance for this sync pair
        """
        self.name = config['name']
        self.local_folder = config['local_folder']
        self.github_repo = config['github_repo']
        self.github_token = self._resolve_token(config['github_token'])
        self.autocommit_time = config.get('autocommit_time', 300)
        self.branch = config.get('branch', 'main')
        self.commit_message_template = config.get('commit_message_template', 'Sync: {timestamp}')
        self.ignore_patterns = config.get('ignore_patterns', [])
        self.logger = logger
        
        # Ensure local folder exists
        Path(self.local_folder).mkdir(parents=True, exist_ok=True)
        
        # Initialize git repository
        self._initialize_git()
        
        # Track last sync time for rate limiting
        self.last_sync_time = 0
        
        # Ensure repository is in valid state
        self._ensure_valid_repository()
        
        # Add lock to prevent concurrent syncs
        self.sync_lock = threading.Lock()
    
    def _ensure_valid_repository(self):
        """
        Ensure the git repository is in a valid state.
        
        This method checks and fixes common issues like invalid HEAD references
        and ensures the repository is ready for sync operations.
        """
        try:
            # Try to access HEAD
            self.repo.head.commit
        except (ValueError, git.exc.BadName):
            self.logger.warning(f"Invalid HEAD in {self.name}, attempting to fix...")
            
            # Check if there are any commits
            commits = list(self.repo.iter_commits())
            if commits:
                # Reset to the first commit
                self.repo.head.reset(commits[0], working_tree=True)
                self.logger.info(f"Reset HEAD to first commit in {self.name}")
            else:
                # Create an empty initial commit if no commits exist
                self.repo.index.commit("Initial empty commit")
                self.logger.info(f"Created initial commit in {self.name}")
            
            # Ensure we're on the correct branch
            try:
                self.repo.git.checkout(self.branch)
            except git.exc.GitCommandError:
                self.repo.git.checkout('-b', self.branch)
    
    def _resolve_token(self, token_config: str) -> str:
        """
        Resolve GitHub token from environment variable.
        
        Args:
            token_config (str): Token configuration (can be direct token or env var)
            
        Returns:
            str: Resolved token value
            
        Raises:
            ValueError: If environment variable is not set
        """
        if token_config.startswith('${') and token_config.endswith('}'):
            env_var = token_config[2:-1]
            token = os.getenv(env_var)
            if not token:
                raise ValueError(f"Environment variable {env_var} not set")
            return token
        return token_config
    
    def _initialize_git(self):
        """
        Initialize or verify git repository setup.
        
        Creates git repository if it doesn't exist, sets up remote origin,
        and handles edge cases like empty repositories or invalid HEAD.
        """
        git_folder = os.path.join(self.local_folder, '.git')
        
        if not os.path.exists(git_folder):
            self.logger.info(f"Initializing git repository in {self.local_folder}")
            self.repo = git.Repo.init(self.local_folder)
            
            # Setup remote
            remote_url = f"https://{self.github_token}@github.com/{self.github_repo}.git"
            self.repo.create_remote('origin', remote_url)
            
            # Create initial commit if folder is not empty
            if any(Path(self.local_folder).iterdir()):
                self.repo.index.add('*')
                if self.repo.index.diff('HEAD'):
                    self.repo.index.commit("Initial commit")
        else:
            self.logger.info(f"Git repository already exists in {self.local_folder}")
            self.repo = git.Repo(self.local_folder)
            
            # Update remote URL if needed
            remote_url = f"https://{self.github_token}@github.com/{self.github_repo}.git"
            if 'origin' not in self.repo.remotes:
                self.repo.create_remote('origin', remote_url)
            else:
                self.repo.remotes.origin.set_url(remote_url)
            
            # Handle case where repo exists but has no commits or invalid HEAD
            try:
                # Try to get the HEAD reference
                self.repo.head.commit
            except (ValueError, git.exc.BadName):
                self.logger.info(f"Repository exists but has no valid HEAD, fixing...")
                
                # Check if there are any commits in the repository
                commits = list(self.repo.iter_commits())
                if commits:
                    # There are commits but HEAD is not valid, reset to first commit
                    self.repo.head.reset(commits[0], working_tree=True)
                else:
                    # No commits exist, create initial commit
                    self.repo.index.add('*')
                    if self.repo.index.diff('HEAD'):
                        self.repo.index.commit("Initial commit")
                    else:
                        # Create empty initial commit if no files to commit
                        self.repo.index.commit("Initial empty commit")
                
                # Ensure we're on the correct branch after creating the first commit
                try:
                    self.repo.git.checkout(self.branch)
                except git.exc.GitCommandError:
                    # Branch doesn't exist, create it
                    self.repo.git.checkout('-b', self.branch)
                
                # Verify HEAD is now valid
                try:
                    self.repo.head.commit
                    self.logger.info(f"Successfully fixed HEAD reference for {self.name}")
                except (ValueError, git.exc.BadName):
                    self.logger.error(f"Failed to fix HEAD reference for {self.name}")
                    raise
    
    def sync(self):
        """
        Perform complete synchronization cycle.
        
        Pulls latest changes, commits local changes if any, and pushes to remote.
        Respects autocommit time limits to prevent excessive commits.
        """
        # Prevent concurrent syncs
        if not self.sync_lock.acquire(blocking=False):
            return
        
        try:
            current_time = time.time()

            # Check if enough time has passed for autocommit
            if current_time - self.last_sync_time < self.autocommit_time:
                return

            try:
                # Always pull latest changes first
                pulled = self._pull_changes()
                if not pulled:
                    self.logger.info(f"No new changes pulled for {self.name}")
                # Then check for local changes and commit/push if needed
                committed_and_pushed = self._commit_and_push()
                if not committed_and_pushed:
                    self.logger.info(f"No local changes to commit or push for {self.name}")
                self.last_sync_time = current_time
            except Exception as e:
                self.logger.error(f"Sync error for {self.name}: {e}")
        finally:
            self.sync_lock.release()
    
    def _pull_changes(self):
        """
        Pull latest changes from remote repository.
        
        Only logs if new commits are fetched/merged.
        Returns True if a pull actually resulted in new changes, False otherwise.
        """
        try:
            # Check if there are unstaged changes
            if self.repo.is_dirty():
                self._commit_and_push()
            # Ensure we're on the correct branch
            current_branch = self.repo.active_branch.name
            if current_branch != self.branch:
                self.repo.git.checkout(self.branch)
            # Get current HEAD before pull
            old_head = self.repo.head.commit.hexsha if self.repo.head.is_valid() else None
            # Perform pull
            pull_result = self.repo.git.pull('origin', self.branch, '--no-rebase', '--strategy-option=theirs')
            # Get new HEAD after pull
            new_head = self.repo.head.commit.hexsha if self.repo.head.is_valid() else None
            if old_head != new_head:
                self.logger.info(f"Pulled new changes for {self.name} (HEAD changed)")
                return True
            return False
        except git.exc.GitCommandError as e:
            self.logger.warning(f"Pull failed for {self.name}: {e}")
            # Handle different types of conflicts
            if "merge conflict" in str(e).lower():
                try:
                    # Abort any ongoing merge
                    self.repo.git.merge('--abort')
                except git.exc.GitCommandError:
                    pass
                # Reset to remote and try again
                try:
                    self.repo.git.reset('--hard', f'origin/{self.branch}')
                    self.repo.git.pull('origin', self.branch, '--no-rebase', '--strategy-option=theirs')
                    self.logger.info(f"Successfully resolved conflicts for {self.name}")
                    return True
                except git.exc.GitCommandError as reset_error:
                    self.logger.error(f"Failed to resolve conflicts for {self.name}: {reset_error}")
            elif "untracked working tree files" in str(e).lower():
                try:
                    # Add all untracked files
                    self.repo.index.add('*')
                    self.repo.index.commit("Add untracked files")
                    # Try pull again
                    self.repo.git.pull('origin', self.branch, '--no-rebase', '--strategy-option=theirs')
                    self.logger.info(f"Successfully resolved untracked files for {self.name}")
                    return True
                except git.exc.GitCommandError as add_error:
                    self.logger.error(f"Failed to resolve untracked files for {self.name}: {add_error}")
            else:
                # Try to reset to a clean state if pull fails
                try:
                    self.repo.git.reset('--hard', f'origin/{self.branch}')
                    self.logger.info(f"Reset {self.name} to remote state")
                    return True
                except git.exc.GitCommandError:
                    self.logger.error(f"Failed to reset {self.name} to remote state")
            return False
    
    def _has_changes(self) -> bool:
        """
        Check if there are uncommitted changes in the repository.
        
        Returns:
            bool: True if there are changes to commit, False otherwise
        """
        try:
            # Check if there's a HEAD commit
            self.repo.head.commit
            return bool(self.repo.index.diff('HEAD') or self.repo.untracked_files)
        except (ValueError, git.exc.BadName):
            # No HEAD commit exists, check for any files to commit
            return bool(self.repo.untracked_files or any(self.repo.index.diff(None)))
        except Exception as e:
            self.logger.warning(f"Error checking for changes in {self.name}: {e}")
            return False
    
    def _commit_and_push(self):
        """
        Commit local changes and push to remote repository.
        
        Only logs if a commit and/or push actually happened.
        Returns True if a commit and/or push actually happened, False otherwise.
        """
        # Add all changes
        self.repo.index.add('*')
        committed = False
        pushed = False
        if self.repo.index.diff('HEAD'):
            # Create commit message with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = self.commit_message_template.format(timestamp=timestamp)
            # Commit
            self.repo.index.commit(commit_message)
            self.logger.info(f"Committed changes for {self.name}: {commit_message}")
            committed = True
        # Get remote HEAD before push
        remote_ref = self.repo.remotes.origin.refs[self.branch] if self.branch in self.repo.remotes.origin.refs else None
        old_remote_head = remote_ref.commit.hexsha if remote_ref else None
        # Push
        push_result = self.repo.remotes.origin.push(self.branch)
        # Get remote HEAD after push
        remote_ref = self.repo.remotes.origin.refs[self.branch] if self.branch in self.repo.remotes.origin.refs else None
        new_remote_head = remote_ref.commit.hexsha if remote_ref else None
        if old_remote_head != new_remote_head:
            self.logger.info(f"Pushed new commits for {self.name}")
            pushed = True
        return committed or pushed


class SyncEventHandler(FileSystemEventHandler):
    """
    File system event handler for real-time sync triggers.
    
    Monitors file system events and triggers sync operations when files are
    created, modified, or deleted. Includes debouncing to prevent excessive syncs.
    """
    
    def __init__(self, sync_pair: SyncPair, logger: logging.Logger):
        """
        Initialize the event handler.
        
        Args:
            sync_pair (SyncPair): The sync pair to trigger syncs for
            logger (logging.Logger): Logger instance
        """
        self.sync_pair = sync_pair
        self.logger = logger
        self.last_event_time = 0
        self.debounce_time = 5  # seconds
    
    def _should_trigger_sync(self) -> bool:
        """
        Check if enough time has passed since last event to trigger sync.
        
        Returns:
            bool: True if sync should be triggered, False otherwise
        """
        current_time = time.time()
        if current_time - self.last_event_time > self.debounce_time:
            self.last_event_time = current_time
            return True
        return False
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        if self._should_trigger_sync():
            self.logger.debug(f"File modified in {self.sync_pair.name}: {event.src_path}")
            self.sync_pair.sync()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        if self._should_trigger_sync():
            self.logger.debug(f"File created in {self.sync_pair.name}: {event.src_path}")
            self.sync_pair.sync()
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return
        
        if self._should_trigger_sync():
            self.logger.debug(f"File deleted in {self.sync_pair.name}: {event.src_path}")
            self.sync_pair.sync()


if __name__ == "__main__":
    """Main entry point for the async sync system."""
    manager = SyncManager()
    try:
        asyncio.run(manager.start_sync())
    except KeyboardInterrupt:
        print("🛑 Sync system stopped")
