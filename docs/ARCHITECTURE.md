# Dex Cognitive Core Architecture

## Overview
Dex (Phase 4) is built as a **Multi-Agent Orchestration Layer** that bridges high-level LLM reasoning with deterministic local execution.

## Core Components

### 1. The Reasoning Layer (Gemini)
Dex uses Google's Gemini 1.5 Pro/Flash to translate natural language into structured plans.
- **Planner Agent**: Orchestrates the planning flow.
- **GeminiPlanner**: Interfaces with the Gemini API to produce JSON-schema constrained execution plans.

### 2. The Context Memory Engine
Memory is handled locally using **SQLite** with semantic retrieval via **sentence-transformers**.
- **Long-term Memory**: Stores task history, notes, and file metadata.
- **Session Context**: Maintains transient state for active conversations.
- **Semantic Search**: Uses cosine similarity over local embeddings for context fetching.

### 3. The Risk & Security Engine
A multi-tier gatekeeper that evaluates every plan step before execution.
- **Classification**: Steps are labeled LOW, MEDIUM, or HIGH risk.
- **Confirmation Flow**: High-risk steps (e.g., `shell_command`) trigger a CLI/Web confirmation request.
- **Policy Enforcement**: Prevents execution of unsanctioned tool/argument combinations.

### 4. Deterministic Executor
The executor consumes the approved plan and invokes local tools. It is strictly decoupled from the LLM to prevent code injection or hallucinated side effects.

### 5. Telemetry & Metrics
Continuous observability into the system's performance.
- **Latency Tracking**: Per-agent and per-tool execution time.
- **Success Metrics**: Success/failure ratios for tools and plans.
- **Risk Distribution**: Monitoring the security profile of user tasks.

## Message Flow
1. **Request**: User sends a command via CLI or Web.
2. **Context**: Memory Engine fetches relevant historical data.
3. **Plan**: Planner + Gemini generate a multi-step execution plan.
4. **Risk Assessment**: Risk Engine scores the plan.
5. **Approval**: User confirms if risk is high; otherwise, auto-approves.
6. **Execution**: Executor runs the steps via local tools.
7. **Verification**: Verifier confirms the outcome matches the plan.
8. **Telemetry**: All metrics are logged for dashboard consumption.
