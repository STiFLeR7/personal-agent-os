# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] — 2026-03-01
### 🚀 Added
- **Discord Control Plane**: Migrated from CLI to Discord-native interface.
- **Structured JSON Planning**: Implemented reliable task decomposition via Gemini.
- **Risk Engine**: Introduced security classification with human-in-the-loop confirmation gating.
- **Catchy Email UI**: Redesigned email notifications with modern HTML/CSS templates.
- **Render Deployment**: Optimized Docker setup for 24/7 uptime on Render with keep-alive logic.
- **Daily Summary**: Automated "Morning Intel Digest" triggered at 08:00 AM IST.
- **Deterministic Executor**: Safe local execution of planned tasks.
- **Verifier + Telemetry**: Post-execution validation and performance logging.

## [0.9.0] — 2026-02-28
### 🔄 Changed
- **Discord Migration**: Introduced Discord Bot Gateway.
- **Channel Routing**: Implemented isolation between `#console`, `#timeline`, and `#priority-feed`.
- **Slash Commands**: Added full support for `/dex run` and `/dex status`.
- **Background Daemon**: Added persistent monitor for time-based reminders.

## [0.5.0] — 2026-02-24
### ✨ Initial Features
- **Local Agent Prototype**: Basic CLI-based command execution.
- **Tool Registry**: Local framework for file operations and note-taking.
- **Gemini Integration**: Initial LLM-based reasoning for task mapping.
