import asyncio
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents import (
    ExecutionPlan,
    ImageGeneratorAgent,
    LinkedInPost,
    PlannerAgent,
)

from pipeline import run_pipeline

app = FastAPI(title="LinkedIn Content Curation API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TopicRequest(BaseModel):
    topic: str
    audience: str = "backend engineers"
    tone: str = "professional yet engaging"


class PlanResponse(BaseModel):
    """Response from POST /plan"""
    job_id: str
    topic: str
    audience: str
    tone: str
    plan: dict
    duration_ms: int


class ExecuteRequest(BaseModel):
    """Request body for POST /execute — carries the plan from /plan"""
    job_id: str
    topic: str
    audience: str
    tone: str
    plan: dict


class ExecuteResponse(BaseModel):
    """Response from POST /execute"""
    job_id: str
    topic: str
    plan: dict
    execution_log: list[dict]   
    post: dict
    image_url: str | None
    image_base64: str | None
    total_duration_ms: int


@app.post("/plan", response_model=PlanResponse)
async def plan_endpoint(request: TopicRequest):
    """
    Step 1 — Run PlannerAgent only.
    Returns the dependency-aware execution plan so the UI can show it
    before execution begins.
    """
    t0 = time.monotonic()
    job_id = str(uuid.uuid4())[:8]

    try:
        planner = PlannerAgent()
        execution_plan: ExecutionPlan = await planner.plan(
            request.topic, request.audience, request.tone
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Planner failed: {exc}")

    return PlanResponse(
        job_id=job_id,
        topic=request.topic,
        audience=request.audience,
        tone=request.tone,
        plan=execution_plan.model_dump(),
        duration_ms=int((time.monotonic() - t0) * 1000),
    )


@app.post("/execute", response_model=ExecuteResponse)
async def execute_endpoint(request: ExecuteRequest):
    """
    Step 2 — Execute the plan returned by /plan.
    Runs the full LangGraph pipeline (search → summarise → generate → edit)
    and image generation in parallel.
    """
    t0 = time.monotonic()

    try:
        plan = ExecutionPlan(**request.plan)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid plan payload: {exc}")

    # Run LangGraph pipeline + image in parallel
    img_agent = ImageGeneratorAgent()
    graph_task = asyncio.create_task(
        run_pipeline(request.topic, request.audience, request.tone, plan)
    )
    image_task = asyncio.create_task(img_agent.generate(request.topic, ""))

    try:
        final_state, (_, image_b64) = await asyncio.gather(
            graph_task, image_task
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution failed: {exc}")

    # Optionally regenerate image with actual headline for a better prompt
    post: LinkedInPost = final_state.get("edited_post") or final_state.get("post")

    step_log: list[dict] = final_state.get("step_log", [])
    execution_log = [
        {
            "step": i + 1,
            "tool": s.get("tool", s.get("node", "unknown")),
            "node": s.get("node", ""),
            "duration_ms": s.get("duration_ms", 0),
            "status": "success",
            "metadata": {k: v for k, v in s.items()
                         if k not in ("node", "tool", "duration_ms")},
        }
        for i, s in enumerate(step_log)
    ]

    return ExecuteResponse(
        job_id=request.job_id,
        topic=request.topic,
        plan=plan.model_dump(),
        execution_log=execution_log,
        post=post.model_dump() if post else {},
        image_url=None,
        image_base64=image_b64,
        total_duration_ms=int((time.monotonic() - t0) * 1000),
    )