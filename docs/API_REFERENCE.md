# Dex API Reference

The Dex Web Dashboard interacts with the backend via a FastAPI REST service. By default, the API runs on `http://127.0.0.1:8000`.

## Endpoints

### 1. System Health
- **GET `/`**: Returns current API status.
- **GET `/state/system`**: Provides a snapshot of all active agents, tasks, and system timestamps.

### 2. Telemetry & Metrics
- **GET `/telemetry/summary`**: Aggregated metrics for the dashboard, including:
  - `success_rate`: Percentage of successful tool calls.
  - `total_tasks`: Cumulative task count.
  - `avg_latency`: Breakout of latency by component (planner, executor).
  - `risk_distribution`: Count of tasks by risk level (low, medium, high).
  - `tool_usage`: Frequency count per tool.

### 3. Task Management
- **GET `/tasks/active`**: List of all tasks currently in the execution pipeline. Includes detailed execution traces and status.

### 4. Memory Exploration
- **GET `/memory/search?q={query}`**: 
  - Performs a semantic search across local memory.
  - Returns a list of matches with similarity scores.

## Schemas
Dex uses **Pydantic v2** for all request and response validation. Refer to `src/agentic_os/coordination/messages.py` for the core message contracts.
