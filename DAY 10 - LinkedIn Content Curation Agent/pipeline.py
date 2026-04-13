
import asyncio
import json
import time
from typing import Annotated, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableLambda
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from models import ExecutionPlan, LinkedInPost, SummaryOutput
from llm import make_llm
from agents import logger, PlannerAgent, GeneratorAgent, EditorAgent
from duckduckgo_search import duckduckgo_search

@tool
async def text_search(topic: str) -> dict:
    """
    Search DuckDuckGo for recent information on the topic using full page text.
    Falls back to Groq LLM knowledge synthesis when search returns thin results.
    Returns dict with keys: topic, results (list of {title, snippet}).
    """
    logger.debug("text_search | topic=%r", topic)
    results: list[dict] = []
    try:
        raw = await asyncio.to_thread(duckduckgo_search, topic, 6)
        logger.debug("text_search | DDG result count=%d", len(raw))
        for r in raw:
            results.append({
                "title": r["title"],
                "snippet": r["full_text"] or r["snippet"],
            })
    except Exception as exc:
        logger.warning("text_search | DDG request failed: %s", exc)
        results.append({"title": "Search error", "snippet": str(exc)})

    logger.debug("text_search | raw result count=%d", len(results))
    # Quality gate: if no substantive abstract returned, run LLM knowledge synthesis
    has_substance = any(
        r["title"] not in ("Search error",) and len(r["snippet"]) > 100
        for r in results
    )
    if not has_substance:
        logger.debug("text_search | thin results, falling back to LLM synthesis")
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a research assistant. Give factual, specific bullet points about recent developments on the topic."),
            ("human", "Provide 6 key recent trends or developments about: {topic}"),
        ])
        chain = fallback_prompt | make_llm(0.4) | RunnableLambda(lambda m: m.content)
        synthesis = await chain.ainvoke({"topic": topic})
        results.append({"title": "Groq Research Synthesis", "snippet": synthesis})

    logger.debug("text_search | final result count=%d", len(results))
    return {"topic": topic, "results": results}

@tool
async def summarizer(topic: str, raw_results_json: str) -> dict:
    """
    Condense raw search results (as JSON string) into 5-7 crisp insight bullets
    suitable for a professional LinkedIn audience.
    Returns dict with keys: topic, bullets.
    """
    _PROMPT = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert research synthesizer. "
            "Condense the raw results into exactly 5-7 specific, insightful bullet points "
            "relevant to a professional LinkedIn audience. No generic filler. "
            'Respond with valid JSON in this exact format:\n'
            '{{"topic": "<topic string>", "bullets": ["bullet 1", "bullet 2", ...]}}'
        )),
        ("human", "Topic: {topic}\n\nRaw results:\n{raw}"),
    ])
    logger.debug("summarizer | topic=%r raw_len=%d", topic, len(raw_results_json))
    chain = _PROMPT | make_llm(0.3).with_structured_output(SummaryOutput, method="json_mode")
    result: SummaryOutput = await chain.ainvoke(
        {"topic": topic, "raw": raw_results_json[:3000]}
    )
    logger.debug("summarizer | bullets=%d", len(result.bullets))
    return result.model_dump()

class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    plan: ExecutionPlan
    topic: str
    audience: str
    tone: str
    search_output: dict | None
    summary_output: dict | None
    post: LinkedInPost | None
    edited_post: LinkedInPost | None
    step_log: list[dict]


async def node_run_search(state: GraphState) -> dict:
    logger.info(">>> node: run_search | topic=%r", state["topic"])
    t0 = time.monotonic()
    result = await text_search.ainvoke({"topic": state["topic"]})
    duration_ms = int((time.monotonic() - t0) * 1000)
    logger.info("<<< node: run_search done | duration_ms=%d results=%d",
                duration_ms, len(result.get("results", [])))
    return {
        "search_output": result,
        "step_log": state["step_log"] + [{
            "node": "run_search",
            "tool": "text_search",
            "duration_ms": duration_ms,
            "result_count": len(result.get("results", [])),
        }],
    }


async def node_run_summarizer(state: GraphState) -> dict:
    t0 = time.monotonic()
    result = await summarizer.ainvoke({
        "topic": state["topic"],
        "raw_results_json": json.dumps(state["search_output"] or {}),
    })
    return {
        "summary_output": result,
        "step_log": state["step_log"] + [{
            "node": "run_summarizer",
            "tool": "summarizer",
            "duration_ms": int((time.monotonic() - t0) * 1000),
            "bullet_count": len(result.get("bullets", [])),
        }],
    }


async def node_run_generator(state: GraphState) -> dict:
    t0 = time.monotonic()
    bullets = (state["summary_output"] or {}).get("bullets", [])
    research = (
        "\n".join(f"• {b}" for b in bullets)
        if bullets else f"Use your knowledge of {state['topic']}"
    )
    agent = GeneratorAgent()
    post = await agent.generate(state["topic"], state["audience"], state["tone"], research)
    return {
        "post": post,
        "step_log": state["step_log"] + [{
            "node": "run_generator",
            "tool": "content_generator",
            "duration_ms": int((time.monotonic() - t0) * 1000),
            "headline": post.headline[:70],
        }],
    }


async def node_run_editor(state: GraphState) -> dict:
    t0 = time.monotonic()
    agent = EditorAgent()
    edited = await agent.edit(state["post"])
    return {
        "edited_post": edited,
        "step_log": state["step_log"] + [{
            "node": "run_editor",
            "tool": "content_editor",
            "duration_ms": int((time.monotonic() - t0) * 1000),
            "headline": edited.headline[:70],
        }],
    }


def build_executor_graph():
    builder = StateGraph(GraphState)
    builder.add_node("run_search", node_run_search)
    builder.add_node("run_summarizer", node_run_summarizer)
    builder.add_node("run_generator", node_run_generator)
    builder.add_node("run_editor", node_run_editor)
    builder.set_entry_point("run_search")
    builder.add_edge("run_search", "run_summarizer")
    builder.add_edge("run_summarizer", "run_generator")
    builder.add_edge("run_generator", "run_editor")
    builder.add_edge("run_editor", END)
    return builder.compile()


EXECUTOR_GRAPH = build_executor_graph()


async def run_pipeline(
    topic: str,
    audience: str,
    tone: str,
    plan: ExecutionPlan,
) -> GraphState:
    """Entry point for FastAPI /execute. Runs the compiled LangGraph."""
    initial: GraphState = {
        "messages": [],
        "plan": plan,
        "topic": topic,
        "audience": audience,
        "tone": tone,
        "search_output": None,
        "summary_output": None,
        "post": None,
        "edited_post": None,
        "step_log": [],
    }
    return await EXECUTOR_GRAPH.ainvoke(initial)