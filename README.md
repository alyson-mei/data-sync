# Data Sync System

A scalable Python-based data synchronization system that automatically syncs local folders with GitHub repositories. This system provides real-time file monitoring, configurable sync intervals, and secure token-based authentication with GitHub-first conflict resolution.

## ✨ Features

- 🔄 **Real-time synchronization** with file system monitoring and debouncing
- ⚙️ **Configuration-based setup** for multiple folder-repo pairs
- 🔐 **Secure token management** using environment variables
- 🕒 **Configurable autocommit times** per sync pair
- 📊 **Comprehensive logging** with colored console and file output
- 🛡️ **GitHub-first conflict resolution** - remote changes take precedence
- 📱 **Command-line interface** for easy management
- 🧪 **Comprehensive test suite** for verification

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python setup.py
```

### 2. Configure Sync Pairs
```bash
python cli.py setup documents /home/user/documents username/documents-repo GITHUB_TOKEN_1
```

### 3. Start Sync System
```bash
python cli.py start
```

### 4. Monitor Status
```bash
python cli.py status
```

## 📁 Project Structure

```
data_sync_system/
├── sync_manager.py      # Core sync engine
├── cli.py              # Command-line interface
├── test_sync.py        # Test suite
├── setup.py            # Setup script
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## ⚙️ Configuration

The system uses a YAML configuration file (`config.yaml`) to define sync pairs:

```yaml
sync_pairs:
  - name: "documents_sync"
    local_folder: "/home/user/documents"
    github_repo: "username/documents-repo"
    github_token: "${GITHUB_TOKEN_1}"
    autocommit_time: 300  # 5 minutes
    branch: "main"
    commit_message_template: "Auto-sync: {timestamp}"
    ignore_patterns:
      - "*.tmp"
      - ".DS_Store"

global:
  sync_interval: 60  # seconds
  max_retries: 3
  retry_delay: 10
  log_level: "INFO"
  log_file: "sync.log"
```

## 🛠️ CLI Commands

### Setup a New Sync Pair
```bash
python cli.py setup <name> <local_folder> <github_repo> <token_env> [options]
```

**Options:**
- `--autocommit-time <seconds>`: Time between commits (default: 300)
- `--branch <branch>`: Git branch (default: main)
- `--commit-template <template>`: Commit message template
- `--ignore-patterns <patterns>`: Comma-separated ignore patterns
- `--config <file>`: Configuration file path

### List All Sync Pairs
```bash
python cli.py list [--config <file>]
```

### Show Sync Status
```bash
python cli.py status [--config <file>]
```

### Start Sync System
```bash
python cli.py start [--config <file>]
```

### Test a Sync Pair
```bash
python cli.py test <name> [--config <file>]
```

## 🔐 GitHub Token Setup

1. **Create a GitHub Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a new token with `repo` permissions
   - Copy the token

2. **Set Environment Variable:**
   ```bash
   export GITHUB_TOKEN_1=your_token_here
   ```
   
   Or add to your `.env` file:
   ```
   GITHUB_TOKEN_1=your_token_here
   ```

## 🔄 Sync Strategy

The system implements a **GitHub-first conflict resolution strategy**:

1. **Pull First**: Always pulls latest changes from remote
2. **Commit Local**: Commits any local changes
3. **Push**: Pushes local commits to remote
4. **Conflict Resolution**: Uses `--strategy-option=theirs` to prioritize remote changes

### Sync Flow
```
File Change Detected → Pull Remote → Commit Local → Push → Log
```

## 📊 Logging

The system provides comprehensive logging:

- **Console Output**: Colored logs for real-time monitoring
- **File Logging**: Persistent logs in `sync.log`
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Log Format
```
2025-08-07 23:01:42 - DataSync - INFO - Pulling latest changes for documents_sync
2025-08-07 23:01:43 - DataSync - INFO - Successfully pulled changes for documents_sync
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_sync.py
```

Tests include:
- ✅ Configuration loading
- ✅ Git repository initialization
- ✅ CLI functionality
- ✅ Basic sync operations

## 🔧 Advanced Usage

### Multiple Sync Pairs

Configure multiple sync pairs with different settings:

```yaml
sync_pairs:
  - name: "documents"
    local_folder: "/home/user/documents"
    github_repo: "username/documents"
    github_token: "${GITHUB_TOKEN_1}"
    autocommit_time: 300
    
  - name: "code"
    local_folder: "/home/user/code"
    github_repo: "username/code"
    github_token: "${GITHUB_TOKEN_2}"
    autocommit_time: 60  # More frequent for code
    ignore_patterns:
      - "__pycache__"
      - "*.pyc"
```

### Custom Ignore Patterns

Configure files to ignore during sync:

```yaml
ignore_patterns:
  - "*.tmp"
  - ".DS_Store"
  - "*.log"
  - "__pycache__"
  - ".env"
```

### Custom Commit Messages

Use templates for commit messages:

```yaml
commit_message_template: "Auto-sync from {timestamp}"
```

## 🛡️ Error Handling

The system includes robust error handling:

- **Network Issues**: Automatic retry with exponential backoff
- **Git Conflicts**: GitHub-first resolution with fallback reset
- **Token Issues**: Clear error messages for authentication problems
- **File Permissions**: Detailed error reporting

## 🔒 Security Considerations

- **Token Security**: Use environment variables, never hardcode tokens
- **File Permissions**: Ensure proper read/write permissions on sync folders
- **Network Security**: Use HTTPS for all GitHub communications
- **Log Security**: Be careful with log files that might contain sensitive information

## 🐛 Troubleshooting

### Common Issues

1. **"Token not found" error:**
   - Ensure environment variable is set
   - Check `.env` file exists and is readable

2. **"Git repository not found":**
   - Ensure GitHub repository exists
   - Check repository permissions for your token

3. **"Permission denied":**
   - Check folder permissions
   - Ensure write access to sync directories

4. **"Network timeout":**
   - Check internet connection
   - Verify GitHub API access

### Debug Mode

Enable debug logging:

```yaml
global:
  log_level: "DEBUG"
```

## 📈 Performance

- **File Monitoring**: Real-time with 5-second debouncing
- **Sync Intervals**: Configurable per repository (default: 60 seconds)
- **Memory Usage**: Minimal overhead for file watching
- **Network**: Efficient git operations with conflict resolution

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆕 Recent Updates

### v2.0 - Clean Code Release
- ✨ **Improved Documentation**: Comprehensive docstrings and comments
- 🧹 **Code Cleanup**: Removed unnecessary imports and functions
- 🔧 **Better Error Handling**: More robust conflict resolution
- 📊 **Enhanced Logging**: Clearer log messages and better formatting
- 🧪 **Improved Tests**: More comprehensive test coverage
- 🚀 **Performance**: Optimized sync operations and file monitoring

### Key Improvements
- **GitHub-First Strategy**: Remote changes always take precedence
- **Debounced File Watching**: Prevents excessive sync operations
- **Comprehensive Logging**: Both console and file logging
- **Robust Error Recovery**: Automatic conflict resolution
- **Clean Architecture**: Well-documented, maintainable code
