<p align="center">
  <img src="assets/dex-icon.png" width="120" alt="Dex Logo">
</p>

<h1 align="center">Dex | Your Personal Discord Cognitive Bot</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-v1.0-blue?style=for-the-badge" alt="v1.0">
  <img src="https://img.shields.io/badge/Deployment-Render_24/7-brightgreen?style=for-the-badge" alt="Render">
  <img src="https://img.shields.io/badge/LLM-Gemini_2.0_Flash-orange?style=for-the-badge" alt="Gemini 2.0">
</p>

<p align="center">
  <strong>A local-first, privacy-focused cognitive control plane optimized for Discord.</strong><br>
  Dex transforms natural language into deterministic system actions, living entirely within your private Discord server.
</p>

---

## 📖 Overview

Dex is not just another chatbot; it is a **Cognitive Operating System** wrapper. It bridges the gap between high-level reasoning (LLM) and deterministic execution (Local Tools). By leveraging **Discord** as a native UI, Dex provides an always-accessible, secure, and organized interface for managing your digital life—from setting reminders and taking notes to executing system-level operations.

### Why Dex?
- **Ubiquity**: Access your system from Mobile, Desktop, or Web via Discord.
- **Reliability**: Uses Gemini 2.0 Flash for structured JSON-based planning.
- **Security**: Built-in Risk Engine with mandatory Human-in-the-Loop confirmations.
- **Privacy**: All task execution happens locally or on your private cloud instance.

---

## 🏗 Core Architecture

Dex operates on a **Proposal-Execution Split** architecture to ensure safety and precision.

1.  **Ingestion**: Receives commands via Discord Slash Commands in `#console`.
2.  **Reasoning**: **Gemini 2.0 Flash** decomposes the request into a structured `ExecutionPlan`.
3.  **Safety Check**: The **Risk Engine** classifies the task (Low/Medium/High).
4.  **Confirmation**: High-risk tasks pause for a UI-based button confirmation in `#priority-feed`.
5.  **Execution**: The **ExecutorAgent** runs the specific Python tools on the host system.
6.  **Verification**: The **VerifierAgent** audits the result and posts a summary to `#timeline`.

---

## 🚀 Key Features

### 📡 Discord-Native Interface
- **Channel Routing**: Clean separation of concerns between `#console`, `#timeline`, `#priority-feed`, and `#reminders`.
- **Interactive UI**: native buttons for approving or cancelling dangerous system operations.
- **Real-time Telemetry**: Monitor system health and performance with `/dex telemetry`.

### 🧠 Cognitive Capabilities
- **Gemini 2.0 Planning**: High-confidence tool selection and argument mapping.
- **Local Memory**: Semantic search and retrieval of past interactions and notes.
- **Daemon Services**: A background monitor for time-based alerts and daily intel digests.

### 📧 Smart Communication
- **Professional Digests**: Automated **Morning Intel Digest** at 08:00 AM IST.
- **Catchy Email UI**: High-end HTML email templates for all outbound notifications.

---

## 📦 Deployment & Setup

### Render Deployment (Recommended)
Dex is optimized for **Render Web Services**, staying active 24/7 via a custom keep-alive loop.

1.  **Fork/Clone** the repository.
2.  Create a new **Web Service** on Render (Docker Runtime).
3.  Set the following **Environment Variables**:
    - `RENDER_EXTERNAL_URL`: Your service URL.
    - `GEMINI_API_KEY`: Your Google AI Studio key.
    - `DISCORD_BOT_TOKEN`: From Discord Developer Portal.
    - `NOTIFY_SMTP_PASSWORD`: Google App Password for Gmail.

### Local Docker Setup
```bash
docker-compose up -d --build
```

---

## ✅ Implementation Roadmap

| Feature | Status | Description |
| :--- | :---: | :--- |
| **Discord Control Plane** | ✅ | Full migration to Discord UI |
| **Gemini 2.0 Integration** | ✅ | JSON-constrained planning logic |
| **Catchy Email Engine** | ✅ | Professional HTML template system |
| **Render Keep-Alive** | ✅ | 24/7 uptime on free tier |
| **WhatsApp Integration** | ⏳ | Twilio-based notification bridge |
| **Desktop Dashboard** | ⏳ | Next.js visual telemetry dashboard |

---

## 🛡 Security & Ethics
- **Deterministic Bounds**: Dex never executes raw shell strings from an LLM without your direct button click.
- **Local Persistence**: Your notes and reminders stay in `.agentic_os/`, never uploaded to a cloud database.
- **Zero-Cloud Execution**: Tools run in your local environment; only reasoning is sent to Gemini.

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<p align="center">
  Built with ❤️ for the future of personal AI.
</p>
