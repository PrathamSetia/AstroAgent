from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ── Import our tools ──────────────────────────────────────────────────────────
from tools.geocode_place import geocode_place as _geocode_place
from tools.compute_birth_chart import compute_birth_chart as _compute_birth_chart
from tools.get_daily_transits import get_daily_transits as _get_daily_transits
from tools.knowledge_lookup import knowledge_lookup as _knowledge_lookup

# ── Wrap tools for LangChain ──────────────────────────────────────────────────
# The @tool decorator tells LangChain the name, description, and parameters
# so the LLM knows when and how to call each one.

@tool
def geocode_place(place_name: str) -> str:
    """Convert a place name to latitude, longitude, and timezone.
    Use this before computing a birth chart when you have a place name."""
    result = _geocode_place(place_name)
    return json.dumps(result)

@tool
def compute_birth_chart(date: str, time: str, place: str) -> str:
    """Compute a natal birth chart given date (YYYY-MM-DD), time (HH:MM),
    and place of birth. Returns planetary positions in zodiac signs.
    Use this when a user provides their birth details."""
    result = _compute_birth_chart(date, time, place)
    return json.dumps(result)

@tool
def get_daily_transits(natal_chart_json: str, date: str = None) -> str:
    """Get today's planetary transits and their aspects to a natal chart.
    natal_chart_json: the JSON string output from compute_birth_chart.
    Use this for daily horoscope or 'energy today' questions."""
    try:
        natal_chart = json.loads(natal_chart_json)
    except Exception:
        return json.dumps({"error": "Invalid natal chart JSON."})
    result = _get_daily_transits(natal_chart, date)
    return json.dumps(result)

@tool
def knowledge_lookup(query: str) -> str:
    """Search the astrology knowledge base for interpretations and meanings.
    Use this to explain planets, signs, aspects, or astrological concepts."""
    result = _knowledge_lookup(query)
    return json.dumps(result)

# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    birth_details: dict
    chart_data: dict

# ── LLM with tools bound ──────────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)
tools = [geocode_place, compute_birth_chart, get_daily_transits, knowledge_lookup]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are Aradhana, a warm and thoughtful AI astrology companion.
You help users understand their birth chart and daily planetary energies.
You speak with care, clarity, and gentle wisdom — like a trusted guide.

You have access to these tools:
- compute_birth_chart: compute a real natal chart from birth date, time, and place
- get_daily_transits: get today's planetary transits relative to a natal chart
- knowledge_lookup: look up meanings of planets, signs, and aspects
- geocode_place: resolve a place name to coordinates (usually called automatically)

Guidelines:
- Always use real tool data — never invent planetary positions
- If birth details are missing, ask for date, time, and place of birth kindly
- For daily energy questions, compute the chart first then get transits
- Astrology is for reflection and guidance only — never present readings as
  medical, legal, or financial certainty
- Keep responses warm, clear, and grounded — not overly mystical"""

# ── Nodes ─────────────────────────────────────────────────────────────────────

def reasoning_node(state: AgentState) -> dict:
    """Main LLM node — reasons and decides whether to call tools."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def router(state: AgentState) -> Literal["tools", "end"]:
    """Decide whether to call tools or end the turn.
    If the last message has tool_calls, route to tools. Otherwise end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"

# ── Tool node (LangGraph built-in) ────────────────────────────────────────────
tool_node = ToolNode(tools)

# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("reasoning")

    # After reasoning: either call tools or end
    graph.add_conditional_edges(
        "reasoning",
        router,
        {"tools": "tools", "end": END}
    )

    # After tools: always go back to reasoning
    graph.add_edge("tools", "reasoning")

    return graph.compile()

app = build_graph()