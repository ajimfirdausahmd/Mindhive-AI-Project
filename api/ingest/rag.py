import json
import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv() 

BASE_DIR = Path(__file__).resolve().parents[1]   
JSONL_PATH = BASE_DIR / "data" / "drinkware.jsonl"
INDEX_DIR = BASE_DIR / "data"

os.makedirs(INDEX_DIR, exist_ok=True)

def row_to_text(r: dict) -> str:
    title = r.get("title") or ""
    price = r.get("price_rm")
    price_s = f"RM{price:,.2f}" if isinstance(price, (int, float)) else ""
    variants = ", ".join([v.get("name", "") for v in r.get("variants", []) if v.get("name")]) or ""
    meas = "; ".join(r.get("measurements", []) or [])
    mats = "; ".join(r.get("materials", []) or [])
    desc = r.get("short_description") or ""
    url = r.get("url") or ""

    parts = [
        f"Title: {title}",
        f"Price: {price_s}" if price_s else "",
        f"Variants: {variants}" if variants else "",
        f"Measurements: {meas}" if meas else "",
        f"Materials: {mats}" if mats else "",
        f"Description: {desc}" if desc else "",
        f"URL: {url}",
    ]
    return "\n".join([p for p in parts if p])

def main():
    if not JSONL_PATH.exists():
        raise FileNotFoundError("Run your scraper first to produce drinkware.jsonl")

    rows = [json.loads(line) for line in JSONL_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise RuntimeError("drinkware.jsonl is empty.")

    # Build Documents with metadata (handy for UI and summaries)
    docs = []
    for r in rows:
        text = row_to_text(r)
        meta = {
            "title": r.get("title"),
            "price_rm": r.get("price_rm"),
            "url": r.get("url"),
            "image": r.get("image"),
        }
        docs.append(Document(page_content=text, metadata=meta))

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    # Pick embeddings
    embeddings = OpenAIEmbeddings()                      

    vectordb = FAISS.from_documents(chunks, embedding=embeddings)
    vectordb.save_local(INDEX_DIR)
    print(f"Saved FAISS index to {INDEX_DIR} (chunks: {len(chunks)})")

if __name__ == "__main__":
    main()