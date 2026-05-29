\# ✦ AstroAgent — Aradhana



A conversational AI astrology companion built with LangGraph, FastAPI, and React.



\## Architecture

React Frontend (port 3000)

↓ SSE streaming

FastAPI Server (port 8000)

↓

LangGraph Agent Graph

├── reasoning\_node  (LLM: llama-3.3-70b-versatile via Groq)

├── tool\_node

│     ├── compute\_birth\_chart  (ephem ephemeris)

│     ├── get\_daily\_transits   (ephem + aspect math)

│     ├── geocode\_place        (geopy + timezonefinder)

│     └── knowledge\_lookup     (keyword RAG over JSON)

└── conditional router → tools or END



\## Setup



\### Prerequisites

\- Python 3.14+

\- Node 18+

\- Groq API key (free at console.groq.com)



\### Backend



```bash

cd backend

python -m venv venv

venv\\Scripts\\activate          # Windows

pip install -r requirements.txt

```



Create `backend/.env`:
GROQ\_API\_KEY=gsk\_kXJsWU6L1mJbyZHgo7sxWGdyb3FYWT2F7sp8XIMt8zt40VO7LWsH



Start the server:

```bash

uvicorn main:api --reload --port 8000

```



\### Frontend



```bash

cd frontend

npm install

npm start

```



Opens at http://localhost:3000



\## Tools



| Tool | Library | Notes |

|------|---------|-------|

| `compute\_birth\_chart` | ephem | Real ephemeris, accurate to \~1 arcminute |

| `get\_daily\_transits` | ephem | Aspects within 6° orb |

| `geocode\_place` | geopy + timezonefinder | Nominatim geocoding |

| `knowledge\_lookup` | JSON + keyword search | 28 curated astrology entries |



\## Evaluation



```bash

cd backend

python eval/run\_eval.py

```



See `eval/results\_log.csv` for run history and `EVALUATION.md` for analysis.



\## Known Limitations



\- Uses `ephem` (Python 3.14 compatible) instead of `pyswisseph` — accurate to \~1 arcminute, not arcsecond

\- Ascendant calculation is simplified (no full Placidus house system)

\- Safety refusal detection needs strengthening (see EVALUATION.md)

\- Groq free tier rate limits can cause latency spikes under load

\- No persistent session storage — chart recomputed each conversation

