# 🤖 Dex - Your Personal AI Operator

A production-grade **local-first** AI agent system that helps you get things done through intelligent task planning, execution, and verification. Designed to listen, remember, and assist.

**"Hey Dex!"** — Voice activation support coming in Phase 3.6

## Overview

Dex is a personal AI control plane that:

- **Accepts tasks** via text commands (voice coming in Phase 5)
- **Remembers everything** - notes, reminders, and task history
- **Executes actions** - file operations, reminders, notes, shell commands
- **Reasons through problems** - decomposes tasks into executable steps
- **Works locally** - no cloud dependency, fully privacy-focused
- **Stays transparent** - shows you exactly what it's doing and where it saved things
- **Actively notifies** - background daemon sends reminders as notifications (Phase 3.5)

## What's New in Phase 3.5

### 🔔 Reactive Reminder System
- **Background daemon** (`dex daemon`) monitors reminders every N seconds
- Reminders **automatically trigger notifications** when due
- **No polling needed** - just set a reminder and the daemon handles it

### 📲 Multi-Channel Notifications  
- **Desktop** - Windows Toast notifications (built-in)
- **Email** - Gmail SMTP integration (optional)
- **WhatsApp** - Twilio REST API (optional)
- **Extensible** - Easy to add more channels

### 🚀 Extended App Launcher
- 30+ applications supported
- WhatsApp, Discord, Teams, Slack, Spotify, Netflix, YouTube, and more
- One-command app launching: `dex run "open whatsapp"`

### ⚡ Enhanced Time Parsing
- Natural language time expressions: "in 5 minutes", "tomorrow at 3pm"
- Fixed deadline: reminders were parsing "1 minute" as "1 hour" - **FIXED**
- UTC timezone support for consistent scheduling across regions

### 🔧 Key Bug Fixes in Phase 3.5
- **Fixed file path mismatch** - Daemon and tool now use same data directory
- **Fixed time parsing regression** - Natural language expressions work correctly
- **Fixed daemon file synchronization** - Real-time reminder monitoring
- **Fixed notification state tracking** - Reminders marked complete after notification

## Quick Feature Tour

### 📌 Reminders
```bash
dex run "remind me to call mom tomorrow at 3pm"
dex run "remind me in 30 minutes to check the mail"
dex run "show all my reminders"

# Daemon support (Phase 3.5)
dex daemon --interval 5        # Monitor reminders every 5 seconds
```

### 📝 Notes
```bash
dex run "take a note about the project deadline"
dex run "save this idea: build a better AI assistant"
dex run "show all my notes"
```

### 📁 File Operations
```bash
dex run "read README.md"
dex run "list files in D:/projects/"
dex run "write this to my-notes.txt"
```

### 🖥️ System Control
```bash
dex run "open chrome"
dex run "open discord"
dex run "list files in the current directory"

# NEW: Extended app launcher (Phase 3.5)
dex run "open whatsapp"
dex run "open teams"
dex run "open spotify"
```

### 🔔 Notifications (NEW - Phase 3.5)
```bash
# Desktop notifications
dex notify --channel desktop "Test message"

# Email notifications (if configured)
dex notify --channel email "Test message"

# WhatsApp notifications (if configured)
dex notify --channel whatsapp "Test message"
```

## Architecture

Dex operates in **5 architectural layers**:

### 1. Input & Perception Layer ✅
- **Text input** via CLI and interactive mode
- **Voice ready** (STT/TTS in Phase 3.5)
- Foundation for future multi-modal input

### 2. Decision Layer (Agentic Core) ✅
- **PlannerAgent**: Understands tasks and creates execution plans
- **ExecutorAgent**: Runs the plan by invoking tools
- **VerifierAgent**: Validates that the task succeeded

### 3. Tool Interface Layer ✅
Unified tool abstraction with:
- **ShellCommandTool** - Execute system commands
- **FileReadTool** - Read file contents
- **FileWriteTool** - Create/write files
- **NoteCreateTool** - Save timestamped notes
- **NoteListTool** - Search and list notes
- **ReminderSetTool** - Create time-based reminders
- **ReminderListTool** - View active reminders
- Stubs ready for: Gmail, Browser, Calendar

### 4. Coordination Layer ✅
Message-driven architecture:
- Async message bus for inter-agent communication
- Request-response pattern with correlation tracking
- Full execution history and observability

### 5. Interoperability Layer ✅
Foundation for future agent-to-agent communication

## Phase 3.5 - Reactive Reminders System

### How It Works

Dex now includes a **background daemon** that actively monitors reminders and sends notifications when they're due.

#### Daemon Architecture

```
┌─────────────────────────────────────────┐
│     Reminder Daemon (dex daemon)        │
│  Polling every 3-5 seconds              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
      ┌────────────────────────┐
      │ Read reminders.json    │
      │ Check due times        │
      └────────┬───────────────┘
               │
        ┌──────▼────────┐
        │ Is Due?       │
        └──┬────────┬───┘
           │        │
          NO      YES
           │        │
           │        ▼
           │   ┌─────────────────────┐
           │   │ Send Notification   │
           │   └────┬────────┬───┬───┘
           │        │        │   │
           │        ▼        ▼   ▼
           │    Desktop  Email  WhatsApp
           │        │        │   │
           │        └────┬───┘   │
           │             ▼       │
           │        ┌─────────────┘
           │        │
           ▼        ▼
      ┌─────────────────┐
      │ Mark Reminded   │
      │ Update JSON     │
      └─────────────────┘
```

#### Notification Channels

1. **Desktop Notifications** (Windows 10+)
   - Windows Toast notifications
   - System tray integration
   - No external dependencies
   ```bash
   dex daemon --interval 3
   ```

2. **Email Notifications** (Gmail)
   - Requires Gmail app password
   - Configure in `.env`:
   ```env
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-16-char-password
   ```

3. **WhatsApp Notifications** (Twilio)
   - Requires Twilio account
   - Configure in `.env`:
   ```env
   TWILIO_ACCOUNT_SID=your-sid
   TWILIO_AUTH_TOKEN=your-token
   TWILIO_NUMBER=+1234567890
   TWILIO_TO_NUMBER=+0987654321
   ```

#### Time Parsing Capabilities

Dex understands flexible time expressions:

```bash
dex run "remind me in 5 minutes to drink water"
dex run "remind me in 2 hours about the meeting"
dex run "remind me in 3 days to call the dentist"
dex run "remind me tomorrow at 3pm to check emails"
dex run "remind me next monday at 2pm for the standup"
```

All times are stored in **UTC** and compared against system time.

#### App Launcher (30+ Applications)

Phase 3.5 includes an extended app launcher:

```bash
# Communication
dex run "open whatsapp"
dex run "open discord"
dex run "open slack"
dex run "open teams"

# Entertainment
dex run "open spotify"
dex run "open netflix"
dex run "open youtube"

# Productivity
dex run "open notion"
dex run "open obsidian"
dex run "open vscode"

# And 20+ more...
```

### 5. Interoperability Layer ✅
Foundation for future agent-to-agent communication

## Installation

```bash
# Clone the repository
git clone https://github.com/STiFLeR7/personal-agent-os.git
cd personal-agent-os

# Install
pip install -e .

# Verify installation
dex --version
```

## Configuration

Create/edit `.env` file:

```env
# Dex Identity
DEX_NAME=Dex
DEX_WAKE_WORD="Hey Dex"
DEX_TIME_ZONE=America/New_York

# Features
DEX_REMINDERS_ENABLED=true      # Reminder scheduling
DEX_NOTES_ENABLED=true          # Note-taking
DEX_DAEMON_ENABLED=true         # Background reminder monitor
DEX_NOTIFICATIONS_ENABLED=true  # Send notifications

# Notifications (Phase 3.5)
DESKTOP_NOTIFICATIONS=true      # Windows Toast (always available)
EMAIL_NOTIFICATIONS=false       # Gmail SMTP
WHATSAPP_NOTIFICATIONS=false    # Twilio

# Gmail Configuration (optional, for email notifications)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Twilio Configuration (optional, for WhatsApp notifications)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_NUMBER=+1234567890
TWILIO_TO_NUMBER=+your-phone-number

# Daemon Settings
DAEMON_CHECK_INTERVAL=5         # Check reminders every N seconds
DAEMON_ENABLE_ON_STARTUP=false  # Auto-start daemon

# Logging
LOG_LEVEL=INFO
LOG_FILE=.agentic_os/logs/dex.log
DEBUG_MODE=false
```

## Usage Examples

### Example 1: Setting a Reminder

```bash
$ dex run "remind me to check emails at 5pm"

✓ TASK EXECUTION COMPLETE

═══ RESULTS ═══

📌 Reminder Set
   ID: rem-1770617171.457489
   Scheduled: 2026-02-09T17:00:00+00:00
   In: 10h 53m

[✓ OK] Verification passed
```

### Example 2: Taking a Note

```bash
$ dex run "take a note: buy groceries - milk, eggs, bread"

✓ TASK EXECUTION COMPLETE

═══ RESULTS ═══

📝 Note Saved
   ID: 2026-02-09t06-05-22-note
   File: D:\personal-agent-os\.agentic_os\notes\2026-02-09t06-05-22-note.md
   Created: 2026-02-09T06:05:22.052401+00:00

[✓ OK] Verification passed
```

### Example 3: Listing Reminders

```bash
$ dex run "show all my reminders"

✓ TASK EXECUTION COMPLETE

═══ RESULTS ═══

📋 Reminders List
   Found 2 reminders:
     • remind me to call mom tomorrow at 3pm @ 2026-02-10T15:00:00+00:00
     • check emails at 5pm @ 2026-02-09T17:00:00+00:00

[✓ OK] Verification passed
```

### Example 4: Reading Files

```bash
$ dex run "read pyproject.toml"

✓ TASK EXECUTION COMPLETE

═══ RESULTS ═══

📖 File Read
   Path: D:\personal-agent-os\pyproject.toml
   Size: 3101 bytes

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dex"
version = "0.2.0"
description = "Dex - Your Personal AI Operator"
...
[cyan]...(truncated)[/cyan]

[✓ OK] Verification passed
```

### Example 5: Interactive Mode

```bash
$ dex run
Running: reminder to review the quarterly report

✓ TASK EXECUTION COMPLETE

═══ RESULTS ═══

📌 Reminder Set
   ID: rem-1770617289.102938
   Scheduled: 2026-02-09T06:08:09.102938+00:00
   In: 1h 0m

[✓ OK] Verification passed
```

## Commands

```bash
# Core Commands
dex run                 # Execute a task
dex run "task here"     # Execute specific task

# Daemon Commands (Phase 3.5)
dex daemon              # Start reminder daemon (5s interval)
dex daemon --interval 10  # Start with custom interval
dex notify              # Test notification system
dex notify --channel desktop "Test"  # Send test desktop notification

# System Information
dex status              # Show system health
dex test                # Run diagnostics
dex config              # Display all settings
dex agents              # List available agents
dex --version           # Show version

# Debug
dex --debug run "task"  # Run with detailed logging
```

## Where Your Data Lives

```
.agentic_os/
├── notes/
│   ├── 2026-02-09t06-05-22-note.md
│   ├── 2026-02-09t06-06-35-note.md
│   └── ...
├── reminders.json          # All scheduled reminders (monitored by daemon)
├── logs/
│   └── dex.log             # System logs
├── cache/                  # Model caches (future)
└── daemon.log              # Daemon activity logs (Phase 3.5)
```

**All data is stored locally. Nothing is uploaded to the cloud.**

#### Reminders File Format

```json
[
  {
    "id": "rem-1771930868.460087",
    "message": "review the quarterly report",
    "scheduled_time": "2026-02-24T14:30:00+00:00",
    "priority": "normal",
    "created_at": "2026-02-24T10:59:26.033891+00:00",
    "is_active": true
  },
  {
    "id": "rem-1771930992.208924",
    "message": "call mom",
    "scheduled_time": "2026-02-25T15:00:00+00:00",
    "priority": "high",
    "created_at": "2026-02-24T11:08:12.208924+00:00",
    "is_active": true
  }
]
```

## Troubleshooting

### Reminders Not Working

1. **Daemon not running** - Start it manually:
   ```bash
   dex daemon --interval 5
   ```

2. **Wrong file path** - Verify reminders are in:
   ```bash
   cat .agentic_os/reminders.json
   ```

3. **Desktop notifications disabled** - Check Windows Settings:
   - Settings → System → Notifications & actions
   - Ensure notifications are enabled

### Email Notifications Not Working

1. **Gmail credentials missing** - Add to `.env`:
   ```env
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-16-char-app-password
   ```

2. **App password incorrect** - Generate new one at:
   - Google Account → Security → App passwords

### WhatsApp Notifications Not Working

1. **Twilio not configured** - Set environment variables:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_NUMBER=+1234567890
   TWILIO_TO_NUMBER=+your-number
   ```

2. **Trial account limits** - Twilio trial only sends to verified numbers

## How It Works

### Task Execution Flow

```
User: "remind me to call mom tomorrow at 3pm"
     ↓
[CLI] Parses task
     ↓
[PlannerAgent] Routes to reminder_set operation
     ↓
[ExecutorAgent] Calls ReminderSetTool
     ↓
[ReminderSetTool] Stores in .agentic_os/reminders.json
     ↓
[VerifierAgent] Validates success
     ↓
[CLI] Displays: "📌 Reminder Set - ID, Scheduled time, Duration"
     ↓
User: Sees exact reminder details and confirmation
```

### Message Flow

```
┌─────────────────────────────────────────┐
│         User Command (CLI)              │
└────────────────┬────────────────────────┘
                 ▼
        ┌──────────────────┐
        │  Message Bus     │
        └────────┬─────────┘
                 ▼
    ┌────────────┼────────────┐
    ▼            ▼            ▼
 PLANNER    EXECUTOR     VERIFIER
   Agent      Agent        Agent
    │            │            │
    └────────────┼────────────┘
                 ▼
        ┌──────────────────┐
        │  Tool Registry   │
        └────────┬─────────┘
                 ▼
      ┌─────────────────────┐
      │  Execute Tool       │
      │  (Save/Read/Schedule)
      └─────────────────────┘
```

## Development

### Project Structure

```
src/agentic_os/
├── __init__.py                      # Package info
├── cli.py                           # User interface + daemon commands
├── config.py                        # Configuration + notifications
├── core/
│   ├── agents.py                    # Agent base classes
│   ├── planner.py                   # Task planning (+ app launcher)
│   ├── executor.py                  # Tool execution
│   ├── verifier.py                  # Result validation
│   ├── planning.py                  # Planning engine
│   └── state.py                     # State management
├── coordination/
│   ├── messages.py                  # Message schemas
│   └── bus.py                       # Message bus
├── daemon/                          # NEW - Phase 3.5
│   ├── __init__.py                  # Daemon exports
│   └── reminder_monitor.py          # Background reminder monitoring
├── notifications/                   # NEW - Phase 3.5
│   ├── __init__.py                  # Notification exports
│   ├── base.py                      # Notification handler interface
│   ├── desktop.py                   # Windows Toast notifications
│   ├── email_notifier.py            # Gmail SMTP notifications
│   └── whatsapp_notifier.py         # Twilio WhatsApp notifications
├── tools/
│   ├── base.py                      # Tool abstractions
│   ├── shell_command.py             # Shell execution
│   ├── file_operations.py           # File I/O
│   ├── notes.py                     # Note management
│   ├── reminders.py                 # Reminder scheduling (enhanced)
│   ├── app_launcher.py              # NEW - App launcher
│   ├── app_tools.py                 # NEW - App launcher tool
│   ├── email_browser.py             # Email/Browser (stubs)
│   ├── time_utils.py                # Time utilities (enhanced)
│   └── __init__.py                  # Tool exports
└── interoperability/
    └── a2a.py                       # Agent-to-agent (future)
```

**Phase 3.5 Additions:**
- `daemon/reminder_monitor.py` - Background daemon monitoring reminders
- `notifications/` - Multi-channel notification system (desktop, email, WhatsApp)
- `tools/app_launcher.py` - 30+ application launcher
- Enhanced time parsing in `tools/reminders.py` and `core/planner.py`

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/test_skeleton.py -v

# Run with coverage
pytest tests/ --cov=src/agentic_os
```

### Code Quality

```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/agentic_os/
```

## Implementation Status

### ✅ Phase 1 - Foundation (Complete)
- Core agents and message bus
- Configuration system
- CLI framework
- End-to-end task execution
- Comprehensive tests

### ✅ Phase 2 - Reliability (Complete)
- Error handling and messages
- Result verification
- Shell command execution
- Proper error reporting

### ✅ Phase 3 - Advanced Tools (Complete)
- 📝 **Full note-taking system** with persistence
- 📌 **Reminder scheduling** with flexible time parsing ("tomorrow 3pm", "in 2h", "in 5 minutes", etc.)
- 📁 **File operations** (read, write, directory listing)
- 💾 **Local storage** for notes and reminders
- 🎯 **Result display** showing exactly what was done

### ✅ Phase 3.5 - Reactive Reminders & Notifications (Complete)
- 🔔 **Background daemon** monitoring reminders in real-time
- 📲 **Desktop notifications** (Windows 10+)
- 📧 **Email notifications** (Gmail SMTP)
- 💬 **WhatsApp notifications** (Twilio REST API)  
- 🎯 **App launcher** - 30+ applications (WhatsApp, Discord, Teams, Spotify, etc.)
- ⚡ **Instant notification** - Reminders trigger automatically when due
- 🔧 **CLI daemon control** - `dex daemon --interval N`

### ⏳ Phase 4 - Advanced Automation (Planned)
- 📧 **Gmail integration** - Read emails, compose, send
- 🌐 **Browser automation** - Navigate, search, extract data  
- 📊 **Dataset analysis** - Load and analyze CSV/Excel files
- 📅 **Calendar integration** - Create events, check availability
- 🔗 **Multi-agent workflows** - Chain multiple tasks together
- 🤖 **Enhanced reasoning** - More complex task decomposition

### ⏳ Phase 5 - Voice & AI Reasoning (Planned)
- 🎤 **Speech-to-Text** (Whisper integration)
- 🔊 **Text-to-Speech** (Piper/gTTS)
- 🎵 **Wake word detection** ("Hey Dex!")
- 🧠 **Advanced reasoning** - Few-shot learning patterns
- 🌍 **Multi-language support** - Spanish, French, German, etc.
- 🎯 **Context awareness** - Remember conversation history
- 📱 **Mobile companion app** - Control Dex from phone

## Hardware Requirements

- **GPU**: Optional (for LLM inference in Phase 4)
- **RAM**: 4GB minimum, 16GB recommended
- **Storage**: 500MB for Dex + space for notes/reminders
- **CPU**: Any modern processor

## Roadmap

```
Phase 1 ✅ │████████████████  Foundation
Phase 2 ✅ │████████████████  Reliability  
Phase 3 ✅ │████████████████  Tools & Reminders
Phase 3.5 ✅ │████████████████ Reactive Reminders & Notifications
Phase 4 ⏳ │███░░░░░░░░░░░░ Advanced Automation
Phase 5 ⏳ │░░░░░░░░░░░░░░░░ Voice Integration & AI Reasoning
```

## Philosophy

> **Dex is not just an assistant. It's your personal AI operator.**

Instead of passive chatbots, Dex actively:
- Remembers what you tell it
- Reminds you when important
- Executes your instructions
- Shows you exactly what it did

## Contributing

Contributions are welcome! Please ensure:
- Type hints throughout
- Comprehensive tests
- Clear documentation
- Follows architectural patterns

## License

MIT License - See LICENSE file

## Support

- 📖 **Documentation**: See `docs/` folder
- 🐛 **Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions  
- 📝 **Examples**: Check `docs/examples/`

---

**Version**: 0.3.0 (Phase 3.5 - Reactive Reminders & Notifications)  
**Last Updated**: February 2026  
**Repository**: https://github.com/STiFLeR7/personal-agent-os
