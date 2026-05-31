# Dex Cognitive Core Architecture (Phase 5)

## Overview
Dex is a **Branded Multi-Agent Orchestration Layer** that bridges high-level LLM reasoning with deterministic local execution. It is optimized for server-wide Discord interactivity and multi-channel proactive communication.

## Core Components

### 1. The Dual-Core Reasoning Layer
Dex uses a tiered reasoning model to balance fidelity and availability.
- **Primary (Gemini 2.0 Flash)**: High-fidelity planner for complex task decomposition.
- **Backup (Groq / Llama 3.3)**: Ultra-fast fallback for conversational queries and daily digest generation when Gemini is throttled.
- **Conversational Engine**: An `on_message` handler with regex-based ping detection for natural server-wide interaction.

### 2. The Hermes Messenger Layer
A robust delivery system that bypasses simple webhooks for native bot identity.
- **Discord Bot REST API**: Posts rich, branded embeds directly to `#console`, `#reminders`, `#priority-feed`, and `#general`.
- **Thumbnail Branding**: Dynamically fetches the `dex-icon.png` from the Render-hosted API.
- **Resend Integration**: Bypasses SMTP blocks on cloud providers to deliver high-end HTML emails.

### 3. The Context & Task Engine
Dex manages your digital state through both semantic memory and structured files.
- **Local Memory**: Semantic retrieval via **sentence-transformers** (optional) and SQLite.
- **TODOTool**: A persistent JSON-based system for tracking and prioritizing daily action items.
- **Integrated Digest**: A background daemon that synthesize reminders, TODOs, and telemetry into a single morning briefing.

### 4. Risk & Security Engine
A multi-tier gatekeeper that evaluates every plan step before execution.
- **Classification**: Steps are labeled LOW, MEDIUM, or HIGH risk.
- **Interactive Confirmation**: High-risk steps trigger a native Discord button UI in `#priority-feed`.

### 5. Double Shield Stability (Render)
Architected to survive the limitations of free-tier cloud hosting.
- **HTTPS Keep-Alive**: The daemon pings the external API URL to prevent service wind-down.
- **Auto-Restart Loop**: A bash-driven supervisor in the Docker container that automatically revives crashed background services.

## Message Flow
1. **Conversational Request**: User pings `@Dex` or issues a `/dex run` command.
2. **Dual-Core Planning**: Planner selects Gemini or Groq to generate a JSON `ExecutionPlan`.
3. **Safety Audit**: Risk Engine scores the plan; high-risk tasks await button click.
4. **Autonomous Execution**: Executor runs Python tools locally within the container.
5. **Branded Verification**: Verifier audits the output and posts a branded embed to `#timeline`.
6. **Proactive Delivery**: Daemon monitors TODOs/reminders and pushes notifications to Discord and Email.
