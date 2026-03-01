# 🧠 How to Use Dex (Discord Cognitive Bot)

Welcome to your Personal AI Operator! Dex is designed to live inside a private Discord server where you are the only user. By organizing its thoughts and actions into different channels, it acts as a clean, powerful operating system for your digital life.

---

## 1. Discord Server Setup

To get the most out of Dex, create a new private Discord Server just for you and the bot. Then, create the following Text Channels:

*   **`#console`**: This is your terminal. You type all your commands here. Dex will *only* listen to commands in this channel.
*   **`#timeline`**: This is Dex's audit log. After it finishes executing a task (like taking a note or listing files), it will post a summary here.
*   **`#priority-feed`**: This is where Dex asks for permission. If you ask it to do something dangerous (like run a shell command), it will post an alert here with a Green/Red button for you to confirm.
*   **`#system-logs`**: (Optional) Use this for monitoring raw system output and bot connection statuses.
*   **`#email-digest`**: (Coming Soon / Phase 3) Where Dex will summarize your inbox.
*   **`#reminders`**: Where you should point your `DISCORD_WEBHOOK_URL` in the `.env` file so that the background daemon can ping you when time is up.

---

## 2. Setting Up the Daemon (Alerts & Reminders)

In order for Dex to actively tap you on the shoulder when a reminder goes off, you need to run the Daemon.
Because we updated your `docker-compose.yml`, starting the system is as simple as:

```bash
docker-compose up -d --build
```

This boots **two** things:
1.  **Dex-Discord**: Listens to your commands in `#console`.
2.  **Dex-Daemon**: Silently watches your `reminders.json` and fires off a webhook to Discord when the time is up.

*(Make sure you have created a Discord Webhook in your server settings and pasted the URL into `DISCORD_WEBHOOK_URL` inside your `.env` file).*

### 3. Deploying to Render
1.  **Service Type**: Web Service
2.  **Runtime**: Docker
3.  **Plan**: Free
4.  **Environment Variables**:
    *   `RENDER_EXTERNAL_URL`: `https://dex-h6tm.onrender.com`
    *   All other keys from your `.env` file.


Dex uses Slash Commands `/` to understand you. Go to the `#console` channel and type `/dex`. You'll see a list of available commands.

### 📝 Taking Notes & Recalling
```text
/dex run save a note about my new project idea: Quantum Computing AI
```
Dex will save this note locally on your machine. You can search for it later:
```text
/dex memory search Quantum
```

### ⏰ Setting Reminders
```text
/dex run remind me to check the oven in 15 minutes
```
*   Dex saves the reminder.
*   The Daemon checks the time.
*   In 15 minutes, a message will pop up in your Discord server alerting you!

### 💻 System & File Commands (Requires Confirmation)
```text
/dex run list all files in D:/personal-agent-os
```
*   Dex realizes this is a system command.
*   It classifies the task as **Medium/High Risk**.
*   It sends a prompt to `#priority-feed` (or replies in the console) asking for your confirmation.
*   Click **Confirm Execution (Green Button)**.
*   Dex runs the command and posts the result in `#timeline`.

### 🤖 Chatting & General Queries
```text
/dex run tell me a joke
```
*   Dex routes this to the **GenericChatTool**.
*   It uses Gemini to generate a response and replies directly to you.

---

## 4. Under the Hood

When you ask Dex to do something, here is what happens:
1.  **Planner**: Gemini looks at your request and available tools (like `file_read`, `reminder_set`, `generic_chat`).
2.  **Risk Engine**: It assigns a risk score.
3.  **Executor**: If safe (or confirmed by you), the executor runs the Python tool on your actual host machine.
4.  **Verifier**: It checks if the tool worked and sends the summary to `#timeline`.

Enjoy your new deterministic AI operating system!
