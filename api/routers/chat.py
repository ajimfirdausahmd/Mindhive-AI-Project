from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.graph_app import build_app  # import from sibling package "app"

router = APIRouter()
graph = build_app()  

class ChatIn(BaseModel):
    session_id: str
    message: str

class ChatOut(BaseModel):
    reply: str
    intent: str | None = None
    tool: str | None = None
    error: str | None = None
    slots: dict | None = None

@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    result = graph.invoke(
        {"messages": [HumanMessage(content=body.message)]},
        config={"configurable": {"thread_id": body.session_id}},
    )
    reply = result["messages"][-1].content
    return ChatOut(
        reply=reply,
        intent=result.get("intent"),
        tool=result.get("tool_name"),
        error=result.get("error"),
        slots=result.get("slots"),
    )