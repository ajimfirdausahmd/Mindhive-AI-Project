from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from typing import TypedDict, Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from typing_extensions import Annotated
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import httpx
import json
import os
import re

load_dotenv()

BACKEND_BASE_URL = os.getenv(
    "BACKEND_BASE_URL",
    "http://127.0.0.1:8000",)

CALC_URL = f"{BACKEND_BASE_URL}/api/v1/calculator"
PRODUCTS_URL = f"{BACKEND_BASE_URL}/api/v1/products"
OUTLETS_URL = f"{BACKEND_BASE_URL}/api/v1/outlets"


#State
class AppState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    intent: Optional[str]            
    slots: Dict[str, Any]            
    next_action: Optional[str]      
    tool_name: Optional[str]        
    tool_result: Optional[Any]       
    error: Optional[str]


llm = ChatOpenAI(model="gpt-4o-mini",api_key=os.getenv("OPENAI_API_KEY"))  


#INTENT & SLOTS

def detect_intent(text: str) -> str:
    t = text.lower().strip()

    product_keys = ["drinkware","bottle","tumbler","cup","thermos","insulated","vacuum","product","products"]
    if any(k in t for k in product_keys) or "drink" in t or "beverage" in t:
        return "products"

    if re.search(r"\boutlet(s)?\b|\bbranch(es)?\b|\bstore(s)?\b|\blocation(s)?\b|\bopening hours?\b|\bclosing time\b|\bhours?\b", t):
    return "outlet_query"

    if re.search(r"\d+\s*[-+*/]\s*\d+", t):
        return "calc"

    return "chitchat"


PRODUCT_KEYWORDS = {"drinkware","bottle","tumbler","cup","thermos","insulated","vacuum"}

CITY_PATTERNS = {r"\bkuala\s+lumpur\b|\bkl\b": "Kuala Lumpur", 
    r"\bpetaling\s+jaya\b|\bpj\b": "Petaling Jaya", 
    r"\bampang\b": "Ampang",}

def update_slots(slots: Dict[str, Any], text: str) -> Dict[str, Any]:
    """Extract structured details from the latest user text and merge into slots."""
    t = text.lower()
    new = dict(slots)

    # Outlet
    for pattern, name in CITY_PATTERNS.items():
        if re.search(pattern, t):
            new["city"] = name
            break

    if re.search(r"\bwangsa\s+maju\b", t):
        new["outlet"] = "Wangsa Maju"

    # Petaling Jaya → Damansara Perdana
    if re.search(r"\bdamansara\s+perdana\b", t):
        new["outlet"] = "Damansara Perdana"

    # Ampang → Bandar Baru Ampang
    if re.search(r"\bbandar\s+baru\s+ampang\b", t):
        new["outlet"] = "Bandar Baru Ampang"


    # Calculator expression 
    expr_match = re.search(r"(?<!\w)(-?\d+(?:\s*[-+*/]\s*-?\d+)+)(?!\w)", t)
    if expr_match:
        new["expr"] = re.sub(r"\s+", "", expr_match.group(1))
    else:
        new.pop("expr", None)

    # Product query 
    if any(k in t for k in PRODUCT_KEYWORDS) or re.search(r"\b(drink|beverage)\b", t):
        new["product_query"] = text.strip()

    return new

# PLANNER NODE 

def planner_node(state: AppState) -> AppState:
    # 1) Get latest user text safely
    last = state["messages"][-1]
    text = last.content if isinstance(last, HumanMessage) else str(last.content)

    # 2) Reset transient fields
    state["error"] = None
    state["tool_result"] = None
    state["tool_name"] = None

    # 3) Intent + slots
    intent = detect_intent(text)
    slots = dict(state.get("slots") or {})  # robust copy

    # Drop irrelevant leftovers by intent
    if intent == "products":
        slots.pop("expr", None); slots.pop("city", None); slots.pop("outlet", None)
    elif intent == "outlet_query":
        slots.pop("expr", None); slots.pop("product_query", None)
    elif intent == "calc":
        slots.pop("product_query", None); slots.pop("city", None); slots.pop("outlet", None)

    # Extract fresh info from this turn
    slots = update_slots(slots, text)

    # 4) Decide next action
    next_action = "reply_only"
    tool_name = None

    if intent == "outlet_query":
        city = slots.get("city"); outlet = slots.get("outlet")
        if not city and not outlet:
            next_action = "ask_clarify"
        else:
            next_action = "use_tool"; tool_name = "outlets"

    elif intent == "calc":
        if slots.get("expr"):
            next_action = "use_tool"; tool_name = "calculator"
        else:
            next_action = "ask_clarify"

    elif intent == "products":
        if slots.get("product_query"):
            next_action = "use_tool"; tool_name = "products"
        else:
            next_action = "ask_clarify"

    # 5) Write back
    state["intent"] = intent
    state["slots"] = slots
    state["next_action"] = next_action
    state["tool_name"] = tool_name
    return state


#  Tool Nodes

def calculator_node(state: AppState) -> AppState:
    expr = state["slots"].get("expr")
    try:
        if not expr:
            raise ValueError("No expression provided.")

        with httpx.Client(timeout=5.0) as client:
            r = client.get(CALC_URL, params={"expr": expr})
        if r.status_code != 200:
            try:
                detail = r.json().get("detail")
            except Exception:
                detail = r.text
            raise RuntimeError(f"Calculator API error: {detail}")

        data = r.json()
        state["tool_result"] = {
            "type": "calculator",
            "expr": data.get("expr", expr),
            "result": data.get("result"),
        }
        state["error"] = None
    except Exception as e:
        state["tool_result"] = None
        state["error"] = f"Calculator error: {e}"
    return state

def products_node(state: AppState) -> AppState:
    q = state["slots"].get("product_query")
    try:
        if not q:
            raise ValueError("No product query provided.")
        with httpx.Client(timeout=20.0) as client:
            r = client.get(PRODUCTS_URL, params={"query": q, "k": 5})
        if r.status_code != 200:
            detail = r.json().get("detail", r.text)
            raise RuntimeError(f"Products API error: {detail}")
        data = r.json()
        items = [
            {"title": h.get("title"), "price": h.get("price_rm"), "url": h.get("url")}
            for h in data.get("hits", [])
        ]
        state["tool_result"] = {
            "type": "products",
            "query": q,
            "items": items,
            "summary": data.get("summary"),
        }
        state["error"] = None
    except Exception as e:
        state["tool_result"] = None
        state["error"] = f"Products error: {e}"
    return state


def outlets_node(state: AppState) -> AppState:
    city = state["slots"].get("city")
    outlet = state["slots"].get("outlet")
    try:
        if not city and not outlet:
            raise ValueError("Missing city or outlet information.")
        if city and outlet:
            query = f"Show opening hours for {outlet} in {city}"
        elif city:
            query = f"Show all outlets in {city}"
        elif outlet:
            query = f"Show opening hours for {outlet}"
        else:
            raise ValueError("Missing city or outlet information.")

        with httpx.Client(timeout=20.0) as client:
            r = client.get(OUTLETS_URL, params={"query": query})

        if r.status_code != 200:
            detail = r.json().get("detail", r.text)
            raise RuntimeError(f"Outlets API error: {detail}")

        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            record = data[0]
            state["tool_result"] = {
                "type": "outlets",
                "city": record.get("city"),
                "outlet": record.get("outlet"),
                "hours": f"Opens {record.get('open_time')} / Closes {record.get('close_time')}",
            }
        else:
            raise RuntimeError("No outlet data returned.")

        state["error"] = None

    except Exception as e:
        state["tool_result"] = None
        state["error"] = f"Outlets error: {e}"

    return state

# RESPONDER NODE 

def respond_node(state: AppState) -> AppState:
    intent = state.get("intent")
    slots = state.get("slots") or {}
    next_action = state.get("next_action")
    tool_name = state.get("tool_name")
    tool_result = state.get("tool_result")
    error = state.get("error")

    state.setdefault("messages", [])

    if next_action == "ask_clarify":
        if intent == "outlet_query":
            if not slots.get("city"):
                text = "Which city do you mean? (e.g., Petaling Jaya)"
            elif not slots.get("outlet"):
                city = slots.get("city", "that city")
                text = f"Which outlet in {city}? (e.g., SS2)"
            else:
                text = "Could you share the missing details?"
        elif intent == "calc":
            text = "Please provide a valid arithmetic expression (e.g., 12*3)."
        elif intent == "products":
            text = "What drinkware are you looking for? (e.g., bottle, tumbler)"
        else:
            text = "Could you clarify your request?"
        state["messages"].append(AIMessage(content=text))
        return state

    if next_action == "use_tool":
        if error:
            text = f"{error}. Could you rephrase or provide the correct info?"
            state["messages"].append(AIMessage(content=text))
            return state

        if tool_name == "calculator" and tool_result:
            text = f"The answer to {tool_result.get('expr')} is {tool_result.get('result')}."
            state["messages"].append(AIMessage(content=text))
            return state

        if tool_name == "products" and tool_result:
            items = tool_result.get("items") or []
            summary = tool_result.get("summary")
            if summary:
                text = summary
            elif items:
                top = items[:5]  
                lines = []
                for it in top:
                    title = it.get("title") or "Unknown item"
                    price = it.get("price")
                    url = it.get("url") or ""
                    price_s = f" (RM{price:,.2f})" if isinstance(price, (int, float)) else ""
                    lines.append(f"- {title}{price_s}" + (f" — {url}" if url else ""))
                text = "Here are some options:\n" + "\n".join(lines) + "\n" \
                       "Want to refine by size, insulation, or budget?"
            else:
                text = "I couldn't find matching drinkware. Want to try a different description (size, insulation, budget)?"
            state["messages"].append(AIMessage(content=text))
            return state

        if tool_name == "outlets" and tool_result:
            city = tool_result.get("city") or slots.get("city") or ""
            outlet = tool_result.get("outlet") or slots.get("outlet") or ""
            hours = tool_result.get("hours") or "Hours unavailable."
            text = f"{outlet} in {city}: {hours}".strip()
            state["messages"].append(AIMessage(content=text))
            return state

        state["messages"].append(AIMessage(content="I couldn’t use the tool just now. Could you rephrase or try again?"))
        return state

    if next_action == "reply_only":
        sys_prompt = (
            "You are a helpful ZUS Coffee assistant. Be concise. "
            "If tool_result is present, you may reference it, otherwise do not invent facts. "
            "Offer how you can help: calculator, products, outlets."
        )
        planner_context = {
            "intent": intent, "next_action": next_action, "tool": tool_name,
            "slots": slots, "error": error,
        }
        messages = [
            SystemMessage(content=sys_prompt),
            SystemMessage(content=f"Planner context: {json.dumps(planner_context, ensure_ascii=False)}"),
            HumanMessage(content="How would you briefly respond to the user now?")
        ]
        ai_msg = llm.invoke(messages)
        state["messages"].append(AIMessage(content=ai_msg.content.strip() or "How can I help you?"))
        return state

    state["messages"].append(AIMessage(content="How can I help you?"))
    return state

def decide_next_node(state: AppState) -> str:
    """Router that decides which node to run after planner_node."""
    if state.get("next_action") != "use_tool":
        return "respond"

    name = state.get("tool_name")
    return {
        "calculator": "call_calculator",
        "products": "call_products",
        "outlets": "call_outlets",
    }.get(name, "respond")    


def build_app():
    graph = StateGraph(AppState)

    graph.add_node("planner", planner_node)
    graph.add_node("call_calculator", calculator_node)
    graph.add_node("call_products", products_node)
    graph.add_node("call_outlets", outlets_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", decide_next_node)
    graph.add_edge("call_calculator", "respond")
    graph.add_edge("call_products", "respond")
    graph.add_edge("call_outlets", "respond")
    graph.add_edge("respond", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Local Demo

if __name__ == "__main__":
    app = build_app()
    tid = "demo-user"

    def turn(text: str):
        out = app.invoke(
            {"messages": [HumanMessage(content=text)]},
            config={"configurable": {"thread_id": tid}},
        )
        print("User:", text)
        print("Bot :", out["messages"][-1].content, "\n")
        return out

    turn("Show opening hours for wangsa maju in Kuala Lumpur")
    turn("What's 12*3?")
    turn("Show me drinkware bottles please.")