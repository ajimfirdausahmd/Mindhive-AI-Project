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
    pytest -q

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

#### 2.4 Frontend Architecture

Located under:

    frontend/

Features:

- Chat UI with threading, avatars, timestamps
- Multiline composer (Enter = send, Shift+Enter = newline)
- Quick commands (/calc, /products, /outlets, /reset)
- Conversation persistence in localStorage
- Calls backend via VITE_BACKEND_URL
- Deployed via Vercel.

#### 2.5 Tests

    tests/
    │
    ├── test_missing_params.py        # Missing city/outlet/expr
    ├── test_api_downtime.py          # Simulated HTTP 500
    └── test_malicious_payload.py     # SQL injection blocked

### 3. API Specification

This section documents all backend endpoints used by the Mindhive AI Assistant, including the Calculator tool, Products RAG pipeline, Outlets Text2SQL pipeline, and Chat (LangGraph agent) endpoint.

#### 3.1 Calculator API

Simple arithmetic evaluator (e.g. 123, 5+92).

Success response

    {
     "expr": "12*3",
     "result": 36
    }

#### 3.2 Products API (RAG over FAISS)

Retrieves drinkware information from the FAISS vector store created from scraped ZUS Coffee product pages.

Success response

    {
       "summary": "Here are some drinkware options:",
       "hits": [
         {
          "title": "ZUS Thermo Steel 500ml",
           "price_rm": 29.9,
           "url": "https://zuscoffee.com/product/thermo-steel-500ml"
         }
      ]
    }

#### 3.3 Outlets API (Text2SQL → SQLite)

Converts natural language questions into SQL using a controlled Text2SQL parser.
Executes against outlets.db and returns store hours.

Success response

     [
        {
            "city": "Kuala Lumpur",
            "outlet": "Wangsa Maju",
            "open_time": "09:00",
            "close_time": "22:00"
        }
     ]

#### 3.4 Chat API (LangGraph Agent)

Main entry point used by frontend UI.

Request body 

    {
    "session_id": "demo-user",
    "message": "Show opening hours for Wangsa Maju in Kuala Lumpur"
    }
    

### 4. Key Trade-offs

This assessment highlights engineering decision-making.
Here are the major choices and trade-offs:

#### 4.1 FAISS vs Pinecone

- Chosen: FAISS (local)
- Reason: Zero cost, easy to run locally for reviewers
- Trade-off: Not horizontally scalable like Pinecone / Weaviate

#### 4.2 SQLite vs PostgreSQL

- Chosen: SQLite
- Reason: Simple, file-based, included in repo
- Trade-off: Not suitable for high write concurrency

#### 4.3 Rule-based Intent Detection vs LLM-based Router

- Chosen: Lightweight rule-based classifier
- Reason: Predictable, fast, easy to test
- Trade-off: Less flexible for ambiguous queries

#### 4.4 Custom Planner vs LangChain Router

- Chosen: Manual planner in LangGraph
- Reason: High clarity; matches assessment’s “agentic planning” requirement
- Trade-off: More code compared to using built-in agents

#### 4.5 Render + Vercel Deployment

Chosen:

- Backend → Render
- Frontend → Vercel

- Reason: Best pairing for FastAPI + React deployment
- Trade-off: Cross-domain CORS, two deployment targets