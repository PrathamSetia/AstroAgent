Evaluation Report — AstroAgent

Summary



| Metric | Run 1 (8b model) | Run 2 (70b model) |

|--------|-----------------|------------------|

| Success rate | 88% (22/25) | 92% (23/25) |

| Correct tool calls | 9/12 | 12/12 |

| Safety refusals | 3/6 | 1/6 |

| Avg tone (1–5) | 3.64 | 3.68 |

| Avg helpfulness (1–5) | 2.84 | 3.40 |

| Latency p50 / p95 | 10.3s / 41.1s | 8.3s / 25.7s |

| Est. tokens | 7,112 | 10,274 |

| Failures | 3 | 2 |



What the eval revealed



Tool calling improved dramatically with the larger model

`llama-3.1-8b-instant` failed to format tool calls correctly 3 times out of 12,

producing malformed JSON that Groq rejected with a 400 error. Switching to

`llama-3.3-70b-versatile` fixed this completely — 12/12 correct tool calls.

This is a meaningful signal: small models should not be used for structured

tool-calling tasks without explicit fine-tuning or output constraints.



Safety refusals are the biggest weakness

Only 1 out of 6 safety cases triggered the refusal detection heuristic.

Investigation shows two causes:

1. The agent does refuse appropriately in its text — but uses different phrasing

than the keywords we check for (e.g. "I'm not qualified" vs "consult a professional").

The heuristic needs broader signal words.

2. Two cases (gc13 legal, gc14 invalid date) failed outright — the agent either

errored or gave a low-quality response. These need prompt engineering attention.



Latency is acceptable but p95 is high

p50 of 8.3s is reasonable for a free-tier LLM with tool calls. p95 of 25.7s

is too high for production — caused by geocoding network latency stacking with

two LLM calls (one to plan, one to respond after tool result). Caching geocode

results would cut this significantly.


Helpfulness scores are conservative

The LLM judge scored helpfulness at 3.40 average. Spot-checking 10 judge

verdicts against my own judgment showed \~70% agreement — the judge tends to

penalise responses that don't explicitly restate all chart data, even when

the response is practically useful. With more time I would refine the rubric

to separate "answered the question" from "included all data".



What I would fix with more time



1.Strengthen safety refusals — add explicit refusal templates to the system

 prompt for medical/legal/financial/certainty requests

2.Cache geocode + chart results— store by (date, time, place) hash to

eliminate redundant API calls and cut p95 latency

3.Broader refusal heuristic — expand keyword list or use a dedicated

classifier for safety checking

4.House system — implement full Placidus houses for more accurate readings

5.Persistent memory— store chart across sessions so users don't re-enter

birth details every time

6.Judge calibration — expand spot-check to 20 cases and report Cohen's

kappa instead of raw agreement rate

