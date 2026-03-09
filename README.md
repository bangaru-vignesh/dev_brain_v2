<<<<<<< HEAD
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

---

## Architecture

### Complete System Workflow

```text
User Browsing
     │
     ▼
Chrome Extension
     │
     │ 1. Capture page activity
     │ (URL, title, timestamp)
     ▼
Local Privacy Filter
     │
     ├── Invalid pages
     │     (chrome:// , blank tabs)
     │        ↓
     │     Ignored
     │
     └── Valid developer content
            │
            ▼
POST /api/events/browser
(FastAPI Backend)
            │
            ▼
AI Classification Service
            │
            ▼
LLM Model (OpenRouter)
            │
            ▼
Classification Output
{
topic,
technology,
domain,
activity_type,
depth,
confidence,
engagement_score,
is_relevant
}
            │
            ▼
Relevance Check
            │
     ├── If NOT relevant
     │       ↓
     │   Event dropped
     │
     └── If relevant
            │
            │
            ├───────────────► Path A: Data Warehouse
            │
            │
            ▼
Path B: Local Skill Engine
```

---

### Path A — Snowflake Analytics Pipeline
This path builds the **analytics system**.

```text
Backend Event
     │
     ▼
Snowflake Connector
     │
     ▼
Bronze Layer
raw_events
(raw JSON storage)
     │
     ▼
Silver Layer
knowledge_events
(clean structured data)
     │
     ▼
Gold Layer
Analytics Tables
     │
     ├ learning_activity_daily
     ├ technology_trends
     └ learning_velocity
     │
     ▼
Analytics API
/api/analytics/*
     │
     ▼
Frontend Dashboard Charts
```

**Purpose of this pipeline:**
* Long-term analytics
* Learning trends
* Technology popularity
* Activity patterns

---

### Path B — Local Skill Intelligence Engine
This path updates the **user’s skill graph in real time**.

```text
Relevant Event
     │
     ▼
Event Deduplication
(prevent repeated spam clicks)
     │
     ▼
Skill Scoring Engine
     │
     │ Calculates:
     │
     │ confidence
     │ depth
     │ engagement
     │ difficulty
     │ activity_type
     │ recency_decay
     │
     ▼
Concept Score Update
(e.g., Python Decorators)
     │
     ▼
Technology Score Update
(e.g., Python)
     │
     ▼
Domain Score Update
(e.g., Backend)
     │
     ▼
SQLite Database
user_skills table
```

**Purpose:**
* Real-time skill tracking
* Concept mastery
* Technology strength
* Domain expertise

---

### Final Dashboard Data Flow

The dashboard receives **two types of data**.

```text
Frontend Dashboard
        │
        │
        ├────────────► GET /api/skills
        │                 │
        │                 ▼
        │           SQLite Skill Graph
        │
        │
        └────────────► GET /api/analytics/*
                          │
                          ▼
                     Snowflake Gold Tables
```

So:
* **SQLite** → Personal skill graph
* **Snowflake** → Analytics insights

---

### DevBrain Executive Summary

> DevBrain captures developer browsing activity through a browser extension, classifies it using an LLM, updates a real-time skill graph in SQLite, and simultaneously streams raw events into a Snowflake data warehouse where a Bronze–Silver–Gold pipeline generates long-term analytics displayed in the dashboard.

---

## Features (MVP)

| Feature | Status |
|---|---|
| JWT Authentication (register / login) | ✅ |
| Knowledge Event Ingestion Pipeline | ✅ |
| Skill Graph Builder (weighted scoring) | ✅ |
| Gap Analysis Engine | ✅ |
| Personalised Recommendation Engine | ✅ |
| Aggregated Dashboard (stats, activity) | ✅ |
| Premium Dark-Mode SPA Dashboard | ✅ |
| Integration Tests (~80% coverage) | ✅ |
| Docker Support | ✅ |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (async) |
| **Database ORM** | SQLAlchemy 2 (async) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Auth** | JWT (python-jose) + bcrypt |
| **Validation** | Pydantic v2 |
| **Config** | pydantic-settings (.env) |
| **Testing** | pytest + pytest-asyncio + httpx |
| **Frontend** | Vanilla HTML/CSS/JS (SPA) |
| **Containerisation** | Docker + Docker Compose |

---

## Project Structure

```
devbrain/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Pydantic settings (env vars)
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   └── security.py         # JWT + password hashing
│   ├── models/
│   │   ├── user.py             # User ORM model
│   │   ├── event.py            # KnowledgeEvent ORM model
│   │   └── skill.py            # UserSkill ORM model
│   ├── schemas/
│   │   ├── auth.py             # Auth request/response schemas
│   │   ├── event.py            # Event schemas
│   │   ├── skill.py            # Skill graph schemas
│   │   └── recommendation.py  # Recommendation + Dashboard schemas
│   ├── api/
│   │   ├── auth.py             # POST /register, /login, GET /me
│   │   ├── events.py           # POST /events, GET /events
│   │   ├── skills.py           # GET /skills, /skills/gaps
│   │   ├── recommendations.py  # GET /recommendations
│   │   └── dashboard.py        # GET /dashboard
│   └── services/
│       ├── user_service.py     # User CRUD
│       ├── event_service.py    # Event pipeline
│       ├── skill_service.py    # Skill graph builder + scoring
│       └── recommendation_service.py  # Recommendation engine
├── frontend/
│   ├── index.html              # Single-page dashboard
│   ├── dashboard.css           # Premium dark-mode styles
│   └── dashboard.js            # API client + rendering
├── tests/
│   └── test_api.py             # Integration test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd devbrain

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
# Edit .env with your settings (optional for dev — defaults work)
```

### 3. Run the Backend

To start the server with optimal performance (bypassing slow Snowflake connection checks) on port 8001:

```powershell
$env:PYTHONPATH="."; $env:PYTHON_CONNECTOR_BYPASS_OCSP_CERT_CHECK="True"; python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

API runs at **http://localhost:8001**
Interactive docs at **http://localhost:8001/api/docs**

### 4. Open the Frontend

Open `frontend/index.html` in your browser (or use Live Server extension in VS Code).

Register an account, then start logging learning events!

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login (OAuth2 form) |
| `GET`  | `/api/auth/me` | Get current user profile |
| `POST` | `/api/events/` | Ingest knowledge event |
| `GET`  | `/api/events/` | List events (paginated) |
| `GET`  | `/api/skills/` | Get skill graph |
| `GET`  | `/api/skills/gaps` | Get gap analysis |
| `GET`  | `/api/recommendations/` | Get personalised recommendations |
| `GET`  | `/api/dashboard/` | Get dashboard aggregation |
| `GET`  | `/api/health` | Health check |

---

## 🧮 Skill Scoring Engine — How It Works

The **Skill Scoring Engine** translates a single learning event (like reading documentation or watching a tutorial) into a quantified **numeric skill gain**. 

It evaluates each event against several heuristic factors, combining them to discover exactly how much your skill has progressed.

### 1. The Core Formula
```text
event_score = confidence × depth_weight × activity_weight × engagement_factor × recency_decay × difficulty_weight × base_multiplier
```
*Example:* 0.95 × 0.8 × 1.0 × 0.7 × 0.95 × 1.1 × 15 ≈ **7.9 learning points gained.**

---

### 2. The Weighting Factors
Each variable serves a specific purpose in evaluating your effort:

* **Confidence Score (0.0 → 1.0):** Measures the AI classifier's certainty about the topic. High certainty (e.g., 0.95) yields full points; low certainty shrinks the impact to prevent bad data from poisoning the skill graph.
* **Depth Weight:** Represents the advanced nature of the material (`Beginner = 0.4`, `Intermediate = 0.7`, `Advanced = 1.0`).
* **Activity Type Weight:** Adjusts points based on your cognitive load (`Browsing = 0.3`, `Watching = 0.6`, `Reading Docs = 0.8`, `Coding = 1.2`).
* **Engagement Score:** Measures how long and deeply you interacted with the content. (A 20-minute video session yields higher engagement than a 10-second site visit).
* **Recency Decay:** Uses an exponential time-decay function (`e^(-days_old / decay_rate)`). Recent actions pull more weight than actions taken months ago.
* **Difficulty Weight:** Harder, abstract topics (e.g. Distributed Systems) gain a slight score multiplier (`1.1x`) over trivial topics.

---

### 3. Diminishing Returns (Anti-Inflation)
Instead of linearly adding points infinitely, the engine applies an asymptotic growth curve to represent actual human mastery.
```text
new_score = old_score + event_score × (1 − old_score / 100)
```
* **Beginner:** `(Score: 10) + 5 event points = 14.5 new score` (Fast growth)
* **Expert:** `(Score: 90) + 5 event points = 90.5 new score` (Slow, stabilized growth requiring profound effort to advance).

---

### 4. Hierarchical Score Propagation
Scores are finally calculated bottom-up across the knowledge graph:
* **Concept:** Python Decorators = 60, Generators = 40, Async = 30
* **Technology:** Python = Average(60, 40, 30) = **43**
* **Domain:** Backend = Average(Python, NodeJS, SQL) = **51**


## Running Tests

```bash
pytest tests/ -v
```

---

## Docker

```bash
docker-compose up --build
```

---

## Roadmap

- [ ] Browser extension for automatic URL ingestion
- [ ] GitHub OAuth + repo analysis
- [ ] YouTube watch history integration
- [ ] AI-powered concept extraction (OpenRouter)
- [ ] Weekly email digest
- [ ] Goal tracking + learning streaks
- [ ] Peer benchmarking
- [ ] Mobile app

---

## PRD

See [PRD.md](PRD.md) for the full Product Requirements Document.

---

<div align="center">
Built with ⬡ for developers who take their growth seriously.
</div>
=======
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

---

## Architecture

### Complete System Workflow

```text
User Browsing
     │
     ▼
Chrome Extension
     │
     │ 1. Capture page activity
     │ (URL, title, timestamp)
     ▼
Local Privacy Filter
     │
     ├── Invalid pages
     │     (chrome:// , blank tabs)
     │        ↓
     │     Ignored
     │
     └── Valid developer content
            │
            ▼
POST /api/events/browser
(FastAPI Backend)
            │
            ▼
AI Classification Service
            │
            ▼
LLM Model (OpenRouter)
            │
            ▼
Classification Output
{
topic,
technology,
domain,
activity_type,
depth,
confidence,
engagement_score,
is_relevant
}
            │
            ▼
Relevance Check
            │
     ├── If NOT relevant
     │       ↓
     │   Event dropped
     │
     └── If relevant
            │
            │
            ├───────────────► Path A: Data Warehouse
            │
            │
            ▼
Path B: Local Skill Engine
```

---

### Path A — Snowflake Analytics Pipeline
This path builds the **analytics system**.

```text
Backend Event
     │
     ▼
Snowflake Connector
     │
     ▼
Bronze Layer
raw_events
(raw JSON storage)
     │
     ▼
Silver Layer
knowledge_events
(clean structured data)
     │
     ▼
Gold Layer
Analytics Tables
     │
     ├ learning_activity_daily
     ├ technology_trends
     └ learning_velocity
     │
     ▼
Analytics API
/api/analytics/*
     │
     ▼
Frontend Dashboard Charts
```

**Purpose of this pipeline:**
* Long-term analytics
* Learning trends
* Technology popularity
* Activity patterns

---

### Path B — Local Skill Intelligence Engine
This path updates the **user’s skill graph in real time**.

```text
Relevant Event
     │
     ▼
Event Deduplication
(prevent repeated spam clicks)
     │
     ▼
Skill Scoring Engine
     │
     │ Calculates:
     │
     │ confidence
     │ depth
     │ engagement
     │ difficulty
     │ activity_type
     │ recency_decay
     │
     ▼
Concept Score Update
(e.g., Python Decorators)
     │
     ▼
Technology Score Update
(e.g., Python)
     │
     ▼
Domain Score Update
(e.g., Backend)
     │
     ▼
SQLite Database
user_skills table
```

**Purpose:**
* Real-time skill tracking
* Concept mastery
* Technology strength
* Domain expertise

---

### Final Dashboard Data Flow

The dashboard receives **two types of data**.

```text
Frontend Dashboard
        │
        │
        ├────────────► GET /api/skills
        │                 │
        │                 ▼
        │           SQLite Skill Graph
        │
        │
        └────────────► GET /api/analytics/*
                          │
                          ▼
                     Snowflake Gold Tables
```

So:
* **SQLite** → Personal skill graph
* **Snowflake** → Analytics insights

---

### DevBrain Executive Summary

> DevBrain captures developer browsing activity through a browser extension, classifies it using an LLM, updates a real-time skill graph in SQLite, and simultaneously streams raw events into a Snowflake data warehouse where a Bronze–Silver–Gold pipeline generates long-term analytics displayed in the dashboard.

---

## Features (MVP)

| Feature | Status |
|---|---|
| JWT Authentication (register / login) | ✅ |
| Knowledge Event Ingestion Pipeline | ✅ |
| Skill Graph Builder (weighted scoring) | ✅ |
| Gap Analysis Engine | ✅ |
| Personalised Recommendation Engine | ✅ |
| Aggregated Dashboard (stats, activity) | ✅ |
| Premium Dark-Mode SPA Dashboard | ✅ |
| Integration Tests (~80% coverage) | ✅ |
| Docker Support | ✅ |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (async) |
| **Database ORM** | SQLAlchemy 2 (async) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Auth** | JWT (python-jose) + bcrypt |
| **Validation** | Pydantic v2 |
| **Config** | pydantic-settings (.env) |
| **Testing** | pytest + pytest-asyncio + httpx |
| **Frontend** | Vanilla HTML/CSS/JS (SPA) |
| **Containerisation** | Docker + Docker Compose |

---

## Project Structure

```
devbrain/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Pydantic settings (env vars)
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   └── security.py         # JWT + password hashing
│   ├── models/
│   │   ├── user.py             # User ORM model
│   │   ├── event.py            # KnowledgeEvent ORM model
│   │   └── skill.py            # UserSkill ORM model
│   ├── schemas/
│   │   ├── auth.py             # Auth request/response schemas
│   │   ├── event.py            # Event schemas
│   │   ├── skill.py            # Skill graph schemas
│   │   └── recommendation.py  # Recommendation + Dashboard schemas
│   ├── api/
│   │   ├── auth.py             # POST /register, /login, GET /me
│   │   ├── events.py           # POST /events, GET /events
│   │   ├── skills.py           # GET /skills, /skills/gaps
│   │   ├── recommendations.py  # GET /recommendations
│   │   └── dashboard.py        # GET /dashboard
│   └── services/
│       ├── user_service.py     # User CRUD
│       ├── event_service.py    # Event pipeline
│       ├── skill_service.py    # Skill graph builder + scoring
│       └── recommendation_service.py  # Recommendation engine
├── frontend/
│   ├── index.html              # Single-page dashboard
│   ├── dashboard.css           # Premium dark-mode styles
│   └── dashboard.js            # API client + rendering
├── tests/
│   └── test_api.py             # Integration test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd devbrain

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
# Edit .env with your settings (optional for dev — defaults work)
```

### 3. Run the Backend

To start the server with optimal performance (bypassing slow Snowflake connection checks) on port 8001:

```powershell
$env:PYTHONPATH="."; $env:PYTHON_CONNECTOR_BYPASS_OCSP_CERT_CHECK="True"; python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

API runs at **http://localhost:8001**
Interactive docs at **http://localhost:8001/api/docs**

### 4. Open the Frontend

Open `frontend/index.html` in your browser (or use Live Server extension in VS Code).

Register an account, then start logging learning events!

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login (OAuth2 form) |
| `GET`  | `/api/auth/me` | Get current user profile |
| `POST` | `/api/events/` | Ingest knowledge event |
| `GET`  | `/api/events/` | List events (paginated) |
| `GET`  | `/api/skills/` | Get skill graph |
| `GET`  | `/api/skills/gaps` | Get gap analysis |
| `GET`  | `/api/recommendations/` | Get personalised recommendations |
| `GET`  | `/api/dashboard/` | Get dashboard aggregation |
| `GET`  | `/api/health` | Health check |

---

## 🧮 Skill Scoring Engine — How It Works

The **Skill Scoring Engine** translates a single learning event (like reading documentation or watching a tutorial) into a quantified **numeric skill gain**. 

It evaluates each event against several heuristic factors, combining them to discover exactly how much your skill has progressed.

### 1. The Core Formula
```text
event_score = confidence × depth_weight × activity_weight × engagement_factor × recency_decay × difficulty_weight × base_multiplier
```
*Example:* 0.95 × 0.8 × 1.0 × 0.7 × 0.95 × 1.1 × 15 ≈ **7.9 learning points gained.**

---

### 2. The Weighting Factors
Each variable serves a specific purpose in evaluating your effort:

* **Confidence Score (0.0 → 1.0):** Measures the AI classifier's certainty about the topic. High certainty (e.g., 0.95) yields full points; low certainty shrinks the impact to prevent bad data from poisoning the skill graph.
* **Depth Weight:** Represents the advanced nature of the material (`Beginner = 0.4`, `Intermediate = 0.7`, `Advanced = 1.0`).
* **Activity Type Weight:** Adjusts points based on your cognitive load (`Browsing = 0.3`, `Watching = 0.6`, `Reading Docs = 0.8`, `Coding = 1.2`).
* **Engagement Score:** Measures how long and deeply you interacted with the content. (A 20-minute video session yields higher engagement than a 10-second site visit).
* **Recency Decay:** Uses an exponential time-decay function (`e^(-days_old / decay_rate)`). Recent actions pull more weight than actions taken months ago.
* **Difficulty Weight:** Harder, abstract topics (e.g. Distributed Systems) gain a slight score multiplier (`1.1x`) over trivial topics.

---

### 3. Diminishing Returns (Anti-Inflation)
Instead of linearly adding points infinitely, the engine applies an asymptotic growth curve to represent actual human mastery.
```text
new_score = old_score + event_score × (1 − old_score / 100)
```
* **Beginner:** `(Score: 10) + 5 event points = 14.5 new score` (Fast growth)
* **Expert:** `(Score: 90) + 5 event points = 90.5 new score` (Slow, stabilized growth requiring profound effort to advance).

---

### 4. Hierarchical Score Propagation
Scores are finally calculated bottom-up across the knowledge graph:
* **Concept:** Python Decorators = 60, Generators = 40, Async = 30
* **Technology:** Python = Average(60, 40, 30) = **43**
* **Domain:** Backend = Average(Python, NodeJS, SQL) = **51**


## Running Tests

```bash
pytest tests/ -v
```

---

## Docker

```bash
docker-compose up --build
```

---

## Roadmap

- [ ] Browser extension for automatic URL ingestion
- [ ] GitHub OAuth + repo analysis
- [ ] YouTube watch history integration
- [ ] AI-powered concept extraction (OpenRouter)
- [ ] Weekly email digest
- [ ] Goal tracking + learning streaks
- [ ] Peer benchmarking
- [ ] Mobile app

---

## PRD

See [PRD.md](PRD.md) for the full Product Requirements Document.

---

<div align="center">
Built with ⬡ for developers who take their growth seriously.
</div>
>>>>>>> 458ad38ffd2a6439d2cbcc35bc35304e37ee233a
