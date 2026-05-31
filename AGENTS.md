# Dex Cognitive Agents Specification (v1.2)

Architecture: **Hermes-Style Dynamic Control Plane**

## 1. PlannerAgent (Dual-Core Reasoning)

**Role:**
*   Decompose conversational requests into structured `ExecutionPlan`.
*   Map user requests to specialized local tools (File, Email, Shell, TODOs).
*   Assign initial risk level based on tool capability.

**Evolution:**
*   **Dual-Core Intelligence**: Uses **Gemini 2.0 Flash** as the primary planner.
*   **Groq Fallback**: Automatically switches to **Llama 3.3 (Groq)** if Gemini hits rate limits, ensuring 100% uptime.
*   Supports conversational `@Dex` pings across all interactive channels.

---

## 2. RiskEngine (Deterministic Guardrails)

**Role:**
*   Security classification (Low/Medium/High).
*   Mandatory "Human-in-the-Loop" gating for all High-risk tasks.
*   Enforces safety policies before arguments reach the Executor.

**High-Risk Operations:**
*   `shell_command`: Direct operating system access.
*   `file_write`: Persistent data modification.
*   `email_compose`: Outbound communication.
*   `todo_manage`: Modifying the master task list.

---

## 3. ExecutorAgent (Autonomous Action)

**Role:**
*   Deterministic execution of approved plan steps using the **Tool Registry**.
*   Argument validation against Pydantic schemas.
*   Isolated execution within Docker-runtime environments.

---

## 4. VerifierAgent (Audit & Post-Action)

**Role:**
*   Post-execution analysis of tool outputs to ensure intent matches result.
*   Audit log generation for the `#timeline` channel.
*   Generates rich Discord embeds with performance metrics (latency, success).

---

## 5. Hermes Background Daemon (ReminderMonitor)

**Role:**
*   **Intelligent Monitoring**: Polls `.agentic_os/reminders.json` and `.agentic_os/todos.json`.
*   **Dynamic Briefings**: Generates the **Morning Intel Digest** via Gemini/Groq at 08:00 AM IST.
*   **Multi-Channel Messenger**: Delivers branded notifications via Discord (native embeds) and HTML Email (Resend).
*   **Double Shield Stability**: Manages the **Render Keep-Alive** loop and auto-restart of all Dex services.
