from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pathlib import Path

import os
             
THIS_FILE = Path(__file__).resolve()
API_DIR = THIS_FILE.parents[1]
INDEX_DIR = API_DIR / "data"

router = APIRouter()

# Response models 
class ProductHit(BaseModel):
    title: Optional[str] = None
    price_rm: Optional[float] = None
    url: Optional[str] = None
    image: Optional[str] = None
    chunk_preview: Optional[str] = None  # short excerpt

class ProductResult(BaseModel):
    ok: bool
    query: str
    k: int
    hits: List[ProductHit]
    summary: Optional[str] = None

#  Lazy singletons
_vectordb = None
_embeddings = None
_llm = None

def _load_vectordb():
    global _vectordb, _embeddings
    if _vectordb is None:
        if not (INDEX_DIR / "index.faiss").exists() or not (INDEX_DIR / "index.pkl").exists():
            raise FileNotFoundError("FAISS index not found in data/. Run ingest script first.")
        _embeddings = OpenAIEmbeddings()
        _vectordb = FAISS.load_local(INDEX_DIR, _embeddings, allow_dangerous_deserialization=True)
    return _vectordb

def _get_llm():
    global _llm
    if _llm is None and os.getenv("OPENAI_API_KEY"):
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    return _llm

@router.get("/products", response_model=ProductResult)
def products(
    query: str = Query(..., description="Natural language question, e.g. 'leak-proof tumbler under RM100'"),
    k: int = Query(5, ge=1, le=10),
):
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        vectordb = _load_vectordb()
        docs = vectordb.similarity_search(query,k = k)

        hits: List[ProductHit] = []
        for d in docs:
            meta = d.metadata or {}
            preview = d.page_content[:260].replace("\n", " ")
            hits.append(ProductHit(
                title=meta.get("title"),
                price_rm=meta.get("price_rm"),
                url=meta.get("url"),
                image=meta.get("image"),
                chunk_preview=preview + ("..." if len(d.page_content) > 260 else "")
            ))

        # Optional short summary (only if API key present)
        llm = _get_llm()
        summary = None
        if llm and hits:
            context_lines = []
            for h in hits:
                price = f"RM{h.price_rm:,.2f}" if isinstance(h.price_rm, (int, float)) else "N/A"
                context_lines.append(f"- {h.title} ({price}) — {h.url}")
            prompt = (
                "Summarize the most relevant ZUS drinkware for the user's need.\n"
                f"User query: {query}\n"
                "Candidates:\n" + "\n".join(context_lines) + "\n\n"
                "Return 2–4 concise bullets focusing on what to choose and why "
                "(capacity, insulation, leak-proof, special lids, price hints)."
            )
            summary = llm.invoke(prompt).content.strip()

        return ProductResult(ok=True, query=query, k=k, hits=hits, summary=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Products retrieval error: {e}")
