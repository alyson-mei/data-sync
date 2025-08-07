# Data Sync System (Alpha)

> **Note:** This project is AI-generated and currently in **alpha**. Use at your own risk. Contributions and feedback are welcome!

---

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

1. **Install dependencies:**
   ```bash
   python setup.py
   ```
2. **Configure sync pairs:**
   ```bash
   python cli.py setup <name> <local_folder> <github_repo> <token_env>
   ```
3. **Start the sync system:**
   ```bash
   python cli.py start
   ```

## 🛠️ CLI Commands

- `python cli.py setup <name> <local_folder> <github_repo> <token_env> [options]`
- `python cli.py list [--config <file>]`
- `python cli.py status [--config <file>]`
- `python cli.py start [--config <file>]`
- `python cli.py test <name> [--config <file>]`

## ⚙️ Configuration

Edit `config.yaml` to define sync pairs and global settings. See the example in the main README.

## 🔐 GitHub Token Setup

1. Create a GitHub Personal Access Token with `repo` permissions.
2. Add it to your `.env` file:
   ```
   GITHUB_TOKEN_1=your_token_here
   ```

## 🛡️ Sync Strategy

- Always pulls remote changes first
- Commits and pushes local changes
- Uses `--strategy-option=theirs` for conflict resolution (GitHub-first)

## 📊 Logging

- Console output with color
- File logging to `sync.log`

## 🧪 Testing

Run the test suite:
```bash
python test_sync.py
```

## ⚠️ Disclaimer

This project is **AI-generated** and in **alpha**. It may contain bugs, incomplete features, or security issues. Please review the code before using in production. Feedback and PRs are welcome!

---

MIT License
