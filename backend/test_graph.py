from agent.graph import app
from langchain_core.messages import HumanMessage

print("Testing LangGraph skeleton...\n")

# Simulate a user sending a message
result = app.invoke({
    "messages": [HumanMessage(content="Hello! Who are you?")],
    "birth_details": {},
    "chart_data": {}
})

# The last message in the list is the agent's reply
reply = result["messages"][-1].content
print(f"Agent reply:\n{reply}")
print("\n✓ Graph runs successfully")