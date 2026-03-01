# 🧠 How to Use Dex (Discord Cognitive Bot)

> **Render Notice:** Dex is deployed on Render for continuous 24/7 availability. No local machine uptime is required for reminders or summaries to trigger.

Welcome to your Personal AI Operator! Dex is designed to live inside a private Discord server where you are the only user. By organizing its thoughts and actions into different channels, it acts as a clean, powerful operating system for your digital life.

---

## 1. Discord Server Setup & Channel Ownership

To get the most out of Dex, create a new private Discord Server and the following Text Channels. Each has a specific, isolated purpose:

*   **`#console`**: **Input Only.** This is your terminal. You type all your commands here. Dex will *only* listen to commands in this channel.
*   **`#timeline`**: **Audit Only.** This is Dex's audit log. After it finishes executing a task, it will post a summary here for your records.
*   **`#priority-feed`**: **Confirmation Only.** If you ask Dex to do something high-risk (like run a shell command), it will post a request here with Green/Red buttons for your approval.
*   **`#system-logs`**: **Internal Debug.** Use this for monitoring raw system output and bot connection statuses.
*   **`#reminders`**: **Alerts.** Point your `DISCORD_WEBHOOK_URL` here so the background daemon can ping you with catchy alerts.

---

## 2. Setting Up the Daemon (Alerts & Reminders)
In order for Dex to actively tap you on the shoulder when a reminder goes off, you need to run the Daemon.
Because we updated your `docker-compose.yml`, starting the system is as simple as:

```bash
docker-compose up -d --build
```

This boots **all services** (API, Discord Bot, and Daemon) in a single pack.

---

## 3. Deploying to Render
1.  **Service Type**: Web Service
2.  **Runtime**: Docker
3.  **Plan**: Free
4.  **Environment Variables**:
    *   `RENDER_EXTERNAL_URL`: `https://dex-h6tm.onrender.com`
    *   All other keys from your `.env` file.

---

## 4. How to Talk to Dex

Dex uses Slash Commands `/` to understand you. Go to the `#console` channel and type `/dex`.

### 📝 Taking Notes & Recalling
```text
/dex run save a note about my new project idea: Quantum Computing AI
```
Dex will save this note locally. You can search for it later:
```text
/dex memory search Quantum
```

### ⏰ Setting Reminders
```text
/dex run remind me to check the oven in 15 minutes
```
*   Dex saves the reminder.
*   In 15 minutes, a catchy notification will appear in your `#reminders` channel!

### 📧 Email Summaries & Sending
```text
/dex run summarize my unread emails
```
*   **Read-only IMAP**: Dex fetches your inbox (if configured).
*   **Summary only**: No raw credentials or full data exposed.
*   **Sending**: You can also ask Dex to send a catchy email:
    ```text
    /dex run send an email to hillaniljppatel@gmail.com with subject "Hello" and body "This is Dex!"
    ```

### 💻 System & File Commands (Requires Confirmation)
```text
/dex run list all files in D:/personal-agent-os
```
*   It classifies the task as **High Risk**.
*   It sends a prompt to **`#priority-feed`** with Green/Red buttons.
*   Dex runs the command *only* after you click the button.

### 🤖 Chatting & General Queries
```text
/dex run tell me a joke
```
*   Dex routes this to the **GenericChatTool** for a natural LLM response.
