import re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import sqlite3
from langchain_openai import ChatOpenAI
from pathlib import Path
import os
import re

router = APIRouter()

THIS_FILE = Path(__file__).resolve()
API_DIR = THIS_FILE.parents[1]
DB_PATH = API_DIR / "data" / "outlets.db"

LLM = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

class OutletResult(BaseModel):
    outlet: str
    city : str
    open_time : str
    close_time : str

@router.get("/outlets", response_model=list[OutletResult])
def outlets(query: str = Query(..., description="Outlets of ZUS in KL and Selangor")):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        prompt = f"""
        Given this schema:
        CREATE TABLE outlets(city TEXT, outlet TEXT, open_time TEXT, close_time TEXT);

        Write ONE SQL SELECT that returns EXACTLY these columns:
        city, outlet, open_time, close_time
        FROM the outlets table only.
        You may add a WHERE clause on city and/or outlet if present in the user query.
        Do NOT use JOIN, PRAGMA, ATTACH, INSERT, UPDATE, DELETE, DROP, ALTER, UNION or comments.
        Return ONLY the SQL.
        User query: {query}
        """

        sql_query = LLM.invoke(prompt).content.strip()

        sql_query = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql_query, flags=re.IGNORECASE | re.DOTALL).strip()
        sql_query = re.sub(r";\s*$", "", sql_query)

        lower = sql_query.lower()

        print("DEBUG SQL =>", repr(sql_query))

        if not re.match(
            r"^select\s+city\s*,\s*outlet\s*,\s*open_time\s*,\s*close_time\s+from\s+outlets\b",
            lower
        ):
            raise ValueError(f"SQL must select city,outlet,open_time,close_time from outlets. Got: {sql_query}")

        forbidden = ["pragma", "attach", "insert", "update", "delete", "drop", "alter", "union", "--", "/*", "*/"]
        if any(tok in lower for tok in forbidden):
            raise ValueError(f"Unsafe SQL generated: {sql_query}")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail="No outlets found for the query.")

        return [
            {"outlet": r[1], "city": r[0], "open_time": r[2], "close_time": r[3]}
            for r in rows
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outlets query error: {e}")