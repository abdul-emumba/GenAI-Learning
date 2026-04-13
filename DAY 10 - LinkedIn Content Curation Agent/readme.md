# LinkedIn Content Curation Agent

Turns a topic into a polished LinkedIn post using Groq, LangChain, LangGraph, FastAPI, and Streamlit.

## Setup

```bash
# Backend
source .env #
uvicorn main:app --reload --port 8000

# Frontend
streamlit run app.py
```

## Agent Roles

| Agent | Role |
|---|---|
| **Planner** | Produces a dependency graph — decides what runs in parallel vs sequence |
| **text_search** | Fetches topic data from DuckDuckGo; falls back to Groq synthesis |
| **summarizer** | Condenses search results into 5–7 insight bullets |
| **Generator** | Writes the LinkedIn post draft (headline, body, hashtags, CTA) |
| **Editor** | Sharpens hook, tone, and hashtags in a second Groq pass |
| **ImageGenerator** | Generates a 1200×627 banner via Pollinations.ai in parallel |

## Why the Planner?

Without it, execution order is hardcoded. The planner lets independent steps (image generation, web search) run in parallel via `asyncio.gather`, makes the pipeline auditable before execution starts, and lets you add new tools without touching pipeline logic.

## Failure Case Observed

When DuckDuckGo returns no content, the Groq fallback sometimes produces markdown-formatted bullets instead of clean JSON — causing `with_structured_output()` to throw a validation error and halt the pipeline. Fixed by wrapping each node's output in a try/except with graceful degradation, and tightening the quality gate to check content substance, not just result count.