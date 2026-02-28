# Security & Privacy Model

## Privacy Philosophy
Dex is designed as a **privacy-first personal AI system**.
- **Local Execution**: All tool execution (shell, files, apps) happens exclusively on your machine.
- **Data Boundaries**: Your local files and notes are never uploaded to the cloud for storage.
- **LLM Usage**: Only the task description and relevant context fragments are sent to the Gemini API for reasoning. Your data is not used for training.

## Risk Engine Model
Dex categorizes all actions into three risk tiers:

### 🟢 LOW RISK
- Read-only operations (e.g., `file_read`, `note_list`).
- Non-destructive metadata queries.
- System status checks.
- **Policy**: Auto-execute.

### 🟡 MEDIUM RISK
- Local file modifications (e.g., `file_write`).
- App launches (e.g., `app_launch`).
- Setting reminders or creating notes.
- **Policy**: Log and execute.

### 🔴 HIGH RISK
- Arbitrary system commands (e.g., `shell_command`).
- Destructive file operations (delete/overwrite).
- Outbound network requests.
- **Policy**: **Human-in-the-Loop confirmation required.**

## Mitigation Strategies
- **Schema Gating**: The Executor only accepts pre-defined tool names and strictly typed arguments.
- **Deterministic Execution**: The LLM *cannot* directly execute code; it can only *propose* a plan that the deterministic Executor must then validate.
- **Isolated State**: The State Manager tracks task lifecycles in memory, preventing cross-task interference.
