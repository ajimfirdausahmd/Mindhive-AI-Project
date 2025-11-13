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

### 1.2 Environment Variables

Create `.env`

    OPENAI_API_KEY=your_key_here

