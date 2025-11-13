 ## Mindhive AI Assistant - Technical Assesment

This project implements an AI-powered assistant for Mindhive’s AI Software Engineer assessment.
It demonstrates multi-turn conversational memory, agentic planning, tool integration, RAG over product data, Text2SQL over outlets DB, error handling, and a working chat UI.

 ### 1. Setup & Run Instructions

This project include

- FastAPI backend (Calculator Tool, Products RAG, Outlets Text2SQL, and Chat Agent)
- LangGraph agent (multi-turn state + planner/controller logic)
- Frontend (React / Vite) for the chat UI
- FAISS vector store for product retrieval
- SQLite outlets database for Text2SQL
- Pytest test suite for unhappy flows

#### 1.1 Requirements

- Python 3.10+
- Node.js 18+
- npm or yarn
- Git

Clone the repository:

    git clone https://github.com/ajimfirdausahmd/mindhive-assessment.git
    cd mindhive-assessment

#### 1.2 Environment Variables

Create `.env`

    OPENAI_API_KEY=your_key_here

#### 1.3 Backend Setup (FastAPI)

Install dependencies

    cd api
    pip install -r requirements.txt

Build drinkware embeddings & outlets DB

    python ingest/web_scraping.py
    python ingest/rag.py

Run backend locally

    uvicorn main:app --reload

#### 1.4 Frontend Setup (React/Vite)

    cd frontend
    npm install
    npm run dev

#### 1.5 Running Tests

    cd tests
    pytest

Covers:

- API downtime (HTTP 500)
- Missing parameters in queries
- SQL injection / malicious payloads
- Sequential memory flow

### 2 Architecture Overview

This AI system is built around Agentic Workflow, multi-turn memory, and tool orchestration.

#### 2.1 High-Level System Diagram

    User Browser
        ↓
    Frontend UI (Vercel / React)
        ↓   REST (JSON)
    Backend (Render / FastAPI)
        ├── /api/v1/calculator  → Calculator Tool
        ├── /api/v1/products    → RAG (FAISS)
        ├── /api/v1/outlets     → Text2SQL → SQLite (outlets.db)
        ↓
    LangGraph State Machine (app/graph_app.py)
        • State (messages + slots)
        • Intent detection
        • Planner decides action
        • Tool calling & error-handling
        • Response generation

#### 2.2 Backend Structure

    api/
    │
    ├── data/
    │   ├── drinkware.jsonl    → Scraped ZUS drinkware data
    │   ├── index.faiss        → FAISS index for vector search
    │   ├── index.pkl          → Metadata store for FAISS
    │   └── outlets.db         → SQLite database for outlets
    │
    ├── ingest/
    │   ├── rag.py             → Embedding + FAISS builder
    │   └── web_scraping.py    → Drinkware + outlets scraping
    │
    ├── routers/
    │   ├── calculator.py      → /api/v1/calculator
    │   ├── products.py        → /api/v1/products
    │   ├── outlets.py         → /api/v1/outlets
    │   └── chat.py            → /chat endpoint (LangGraph controller)
    │
    ├── main.py                → FastAPI app entrypoint
    │
    └── …

#### 2.3 LangGraph Agent

Located at:

    app/graph_app.py

Contains:

- `State`: Representation (`AppState`)
- `messages`: Conversation history
- `slots`: Extracted structured memory (city, outlet, expr, query)
- `intent`: Current intent
- `next_action`: Planner decision (reply, ask, use tool)
- `tool_result`: Data returned from tools
- `error`: Error info for unhappy flows

Planner Node

Decides whether to:

- Ask for missing info
- Call calculator
- Call RAG
- Call Text2SQL
- Or finish with LLM small talk

This is your agentic orchestrator.

Tool Nodes

- `calculator_node`
- `products_node`
- `outlets_node`

Responder Node

Turns internal tool output into natural language.