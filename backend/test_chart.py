from agent.graph import app
from langchain_core.messages import HumanMessage

result = app.invoke({
    'messages': [HumanMessage(content='Compute my birth chart. Born June 15 1990 at 8:30 AM in Delhi, India.')],
    'birth_details': {},
    'chart_data': {}
})
print(result['messages'][-1].content[:300])