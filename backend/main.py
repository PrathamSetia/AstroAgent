from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage
import json
import asyncio

from agent.graph import app as agent_app

# ── App setup ─────────────────────────────────────────────────────────────────
api = FastAPI(title="AstroAgent API", version="1.0.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ─────────────────────────────────────────────────
class Message(BaseModel):
    role: str        # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]
    birth_details: Optional[dict] = {}
    chart_data: Optional[dict] = {}

# ── Health check ──────────────────────────────────────────────────────────────
@api.get("/health")
def health():
    return {"status": "ok", "agent": "AstroAgent v1"}

# ── Main chat endpoint (streaming) ────────────────────────────────────────────
@api.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Accepts conversation history and streams the agent response
    as server-sent events (SSE).
    """

    # Convert incoming messages to LangChain format
    lc_messages = []
    for m in request.messages:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))

    if not lc_messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    state = {
        "messages": lc_messages,
        "birth_details": request.birth_details or {},
        "chart_data": request.chart_data or {},
    }

    async def event_generator():
        try:
            # Run the agent in a thread (LangGraph is sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent_app.invoke, state)

            # Get the final reply
            final_message = result["messages"][-1]
            content = final_message.content or ""

            # Stream word by word for a natural feel
            words = content.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == len(words) - 1 else word + " "
                data = json.dumps({"type": "token", "content": chunk})
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.02)

            # Send tool activity summary
            tool_calls_made = []
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls_made.append(tc["name"])

            if tool_calls_made:
                data = json.dumps({"type": "tools_used", "tools": tool_calls_made})
                yield f"data: {data}\n\n"

            # Signal done
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ── Non-streaming endpoint (simpler, for testing) ─────────────────────────────
@api.post("/chat")
async def chat(request: ChatRequest):
    """Non-streaming chat — returns full response at once."""
    lc_messages = []
    for m in request.messages:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))

    if not lc_messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    state = {
        "messages": lc_messages,
        "birth_details": request.birth_details or {},
        "chart_data": request.chart_data or {},
    }

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, agent_app.invoke, state)

    final = result["messages"][-1].content

    tool_calls_made = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_made.append(tc["name"])

    return {
        "reply": final,
        "tools_used": tool_calls_made,
        "message_count": len(result["messages"])
    }