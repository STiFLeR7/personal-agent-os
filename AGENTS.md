# Dex Cognitive Agents Specification (v1.0)

Architecture: **Discord-Native Control Plane**

## 1. PlannerAgent (Gemini-powered)

**Role:**
*   Decompose natural language into structured `ExecutionPlan`.
*   Map user requests to specific local tools.
*   Assign initial risk level based on tool capability.

**Evolution:**
*   Migrated from raw CLI strings to JSON-schema constrained Gemini 1.5 logic.
*   Supports `generic_chat` fallback for conversational queries.

---

## 2. RiskEngine

**Role:**
*   Security classification (Low/Medium/High).
*   Mandatory "Human-in-the-Loop" gating for High-risk tasks.
*   Enforces confirmation via Discord interactive buttons.

**High-Risk Operations:**
*   `shell_command`: Direct OS access.
*   `file_write`: Persistent data modification.
*   `email_compose`: Outbound communication.

---

## 3. ExecutorAgent

**Role:**
*   Deterministic execution of approved plan steps.
*   Argument validation against Pydantic schemas.
*   Isolated execution within Docker container (Render).

---

## 4. VerifierAgent

**Role:**
*   Post-execution analysis of tool outputs.
*   Audit log generation for the `#timeline` channel.
*   Flags discrepancies between "intended" vs "actual" results.

---

## 5. Background Daemon (ReminderMonitor)

**Role:**
*   Continuous polling of `.agentic_os/reminders.json`.
*   Triggers catchy Discord Webhook alerts.
*   Executes the **Daily Intel Digest (08:00 AM IST)**.
*   Manages the **Render Keep-Alive** self-ping loop.
