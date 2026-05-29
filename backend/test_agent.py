from agent.graph import app
from langchain_core.messages import HumanMessage

def chat(message: str, state: dict = None) -> dict:
    if state is None:
        state = {"messages": [], "birth_details": {}, "chart_data": {}}
    state["messages"].append(HumanMessage(content=message))
    result = app.invoke(state)
    reply = result["messages"][-1].content
    print(f"\nUser: {message}")
    print(f"Aradhana: {reply}\n")
    return result

print("=== Test 1: Simple greeting ===")
chat("Hello! What can you help me with?")

print("=== Test 2: Birth chart request ===")
chat("Can you compute my birth chart? I was born on June 15, 1990 at 8:30 AM in Delhi, India.")

print("=== Test 3: Knowledge question ===")
chat("What does it mean to have Saturn in Capricorn?")