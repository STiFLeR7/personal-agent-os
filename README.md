# 🤖 Dex - Your Personal AI Operator

A production-grade **local-first** AI agent system that helps you get things done through intelligent task planning, execution, and verification. Designed to listen, remember, and assist.

**"Hey Dex!"** — Voice activation support coming in Phase 3.5

## Overview

Dex is a personal AI control plane that:

- **Accepts tasks** via text commands (voice coming soon)
- **Remembers everything** - notes, reminders, and task history
- **Executes actions** - file operations, reminders, notes, shell commands
- **Reasons through problems** - decomposes tasks into executable steps
- **Works locally** - no cloud dependency, fully privacy-focused
- **Stays transparent** - shows you exactly what it's doing and where it saved things

## Quick Feature Tour

### 📌 Reminders
```bash
dex run "remind me to call mom tomorrow at 3pm"
dex run "set a reminder for the meeting in 2 hours"
dex run "show all my reminders"
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
dex run "open settings"
dex run "list files in the current directory"
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
DEX_VOICE_ENABLED=false           # Enable in Phase 3.5
DEX_REMINDERS_ENABLED=true
DEX_NOTES_ENABLED=true

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
├── reminders.json          # All scheduled reminders
├── logs/
│   └── dex.log             # System logs
└── cache/                  # Model caches (future)
```

**All data is stored locally. Nothing is uploaded to the cloud.**

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
├── cli.py                           # User interface
├── config.py                        # Configuration
├── core/
│   ├── agents.py                    # Agent base classes
│   ├── planner.py                   # Task planning
│   ├── executor.py                  # Tool execution
│   ├── verifier.py                  # Result validation
│   ├── planning.py                  # Planning engine
│   └── state.py                     # State management
├── coordination/
│   ├── messages.py                  # Message schemas
│   └── bus.py                       # Message bus
├── tools/
│   ├── base.py                      # Tool abstractions
│   ├── shell_command.py             # Shell execution
│   ├── file_operations.py           # File I/O
│   ├── notes.py                     # Note management
│   ├── reminders.py                 # Reminder scheduling
│   ├── email_browser.py             # Email/Browser (stubs)
│   ├── time_utils.py                # Time utilities
│   └── __init__.py                  # Tool exports
└── interoperability/
    └── a2a.py                       # Agent-to-agent (future)
```

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
- 📌 **Reminder scheduling** with flexible time parsing ("tomorrow 3pm", "in 2h", etc.)
- 📁 **File operations** (read, write, directory listing)
- 💾 **Local storage** for notes and reminders
- 🎯 **Result display** showing exactly what was done
- 🎤 **Voice integration foundation** (ready for Phase 3.5)

### 🔄 Phase 3.5 - Voice (In Planning)
- Speech-to-Text (Whisper)
- Wake word detection ("Hey Dex!")
- Text-to-Speech (Piper/gTTS)
- Voice command execution

### ⏳ Phase 4 - Advanced Automation (Planned)
- Gmail integration
- Browser automation
- Dataset analysis
- Calendar/scheduling
- Multi-agent workflows

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
Phase 3.5 🔄 │██████░░░░░░░░░░ Voice Integration
Phase 4 ⏳ │███░░░░░░░░░░░░ Advanced Tools
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

**Version**: 0.2.0 (Phase 3 - Notes, Reminders, Files)  
**Last Updated**: February 2026  
**Repository**: https://github.com/STiFLeR7/personal-agent-os
