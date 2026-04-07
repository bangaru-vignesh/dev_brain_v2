<div align="center">

```
 ⬡  DevBrain — Personal Learning OS for Developers
```

**Automatically track everything you learn. Quantify your skills. Know exactly what to learn next.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=flat-square)](https://sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## What Is DevBrain?

DevBrain is a **"Second Brain for Builders"** — a personal learning operating system that automatically tracks everything developers learn across the web (YouTube, GitHub, docs, blogs, notes) and converts it into a **structured, quantified skill graph**.

Instead of guessing what you know or what to learn next, DevBrain gives you real answers:

- *"How strong am I in React?"*
- *"What concepts am I missing in Backend development?"*
- *"What should I study this week?"*

With the newly integrated **Frontend Intelligence Layer**, it grades your daily progression and helps adjust your digital diet by presenting a **Learning Health Score** directly onto your home dashboard!

---

## 🚀 Key Features

| Feature | Status | Description |
|---|---|---|
| JWT Authentication Pipeline | ✅ | Fully isolated multi-tenant architecture. |
| AI Privacy Filter (OpenRouter) | ✅ | LLM checks if web traffic is dev-related. Irrelevant traffic is securely dropped. |
| Skill Graph Scoring Engine | ✅ | Calculates mastery using depth, time, confidence, and curve decay logic. |
| **Learning Health Score** | ✅ | Gives a direct 0-100 grade based on your Focus Time and Coding/Learning Ratio. |
| Premium Dark-Mode SPA | ✅ | Glassmorphism dashboard fetching metrics directly from backend stats. |
| Chrome Browser Extension | ✅ | Captures passive web activity with native debounce deduplication. |
| VS Code Extension | ✅ | Tracks active coding files securely via an internal sandboxed environment. |

---

## Architecture

### Complete System Workflow

```text
User Activity (VS Code OR Chrome)
             │
             ▼
Local Privacy Filter (Deduplication & Bounce)
             │
             ▼
      POST /api/events/
      (FastAPI Backend)
             │
             ▼
AI Classification Service (LLM)
             │
      ├── If NOT relevant (e.g. general Google search)
      │       ↓
      │   Event dropped for Privacy
      │
      └── If relevant
             │
             ├───────────────► Path A: Snowflake Data Warehouse
             │
             ▼
Path B: Local Skill Engine ───► Calculates Learning Health Score
```

Every piece of data flows into the dual-path architecture. SQLite rapidly updates the local interface with **Insights** while Snowflake manages massive data transformations.

---

## 📦 Setting up the Agents (Trackers)

DevBrain operates automatically in the background using two distinct sensors safely tied to your user JWT token.

### 1. Browser Extension
- Found in the `extension/` directory.
- Open `chrome://extensions/`, enable **Developer Mode**, and click **Load unpacked**.
- Click the DevBrain popup in your taskbar, and insert your credentials. It will start pinging your dev searches.
- *(Note: It has a 5-second debounce built-in so fast typing in Google's omnibox doesn't spam your database).*

### 2. VS Code Extension
- Found in the `vscode-extension/` directory.
- Open a dedicated terminal inside that folder.
- Run `npm install`, then press `F5` to open the safe Extension Development Sandbox.
- Press `Ctrl+Shift+P` and type `DevBrain: Connect API Key` to link it.

---

## 🛠️ Quick Start (Backend & API)

### 1. Environment

```bash
git clone <your-repo-url>
cd devbrain

python -m venv venv
venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

### 2. Run the Backend Server

To start the server with optimal performance (bypassing slow Snowflake checks) on port 8001:

```powershell
$env:PYTHONPATH="."; $env:PYTHON_CONNECTOR_BYPASS_OCSP_CERT_CHECK="True"; python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

API runs at **http://localhost:8001**
Interactive swagger docs at **http://localhost:8001/api/docs**

### 3. Open the Frontend Dash

Simply navigate to `frontend/index.html` and open it directly in your browser.

> [!WARNING]
> **VS Code Live Server Users:**
> Because the background extensions constantly save data to the root `devbrain.db` file, VS Code Live Server will aggressively auto-reload your browser. To fix this, create a `.vscode/settings.json` file and add `"liveServer.settings.ignoreFiles": ["**/*.db", "**/.logs/**"]`.

---

## 💡 Troubleshooting

* **Q: Why doesn't my data show up in the dashboard?**
  * **A:** Check your emails! If you logged into the extension as `testuser@devbrain.dev` but logged into the frontend as `demo@devbrain.dev`, the data goes strictly to different databases!
* **Q: I searched Google but nothing happened.**
  * **A:** Our AI intentionally sets `is_relevant: False` for broad searches (e.g., cooking recipes) to secure your privacy. Only developer-oriented websites get passed via the pipeline.
* **Q: My VS Code Extension gives an `UnleashProvider` error.**
  * **A:** This is a diagnostic noise emitted from standard extensions (like GitLens) running inside the VS Code development sandbox. Ignore it—your tracker is still successfully capturing!

---

<div align="center">
Built with ⬡ for developers who take their growth seriously.
</div>
