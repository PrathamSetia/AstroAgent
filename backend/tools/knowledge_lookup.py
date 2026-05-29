import json
import os

# Load knowledge base once at import time
_KB_PATH = os.path.join(os.path.dirname(__file__), "astrology_knowledge.json")

with open(_KB_PATH, "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

def knowledge_lookup(query: str, max_results: int = 3) -> dict:
    """
    Search the astrology knowledge base for entries relevant to the query.
    Uses simple keyword matching — fast, transparent, no vector DB needed.
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty."}

    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored = []
    for entry in KNOWLEDGE_BASE:
        score = 0
        # Check keywords
        for kw in entry["keywords"]:
            if kw in query_lower:
                score += 2  # exact keyword match
        # Check topic
        if entry["topic"].lower() in query_lower:
            score += 3
        # Check individual words
        for word in query_words:
            if any(word in kw for kw in entry["keywords"]):
                score += 1

        if score > 0:
            scored.append((score, entry))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_results]

    if not top:
        return {
            "query": query,
            "results": [],
            "message": "No relevant entries found. Try different keywords."
        }

    return {
        "query": query,
        "results": [
            {
                "topic": e["topic"],
                "content": e["content"]
            }
            for _, e in top
        ]
    }