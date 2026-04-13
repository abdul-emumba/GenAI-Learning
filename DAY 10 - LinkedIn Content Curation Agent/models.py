from pydantic import BaseModel, Field
from typing import Literal

# pydantic models for structured output from agents
class PlanStep(BaseModel):
    step: int = Field(description="Step number, 1-indexed")
    tool: Literal[
        "text_search", "summarizer",
        "content_generator", "content_editor", "image_generator"
    ] = Field(description="Tool to invoke at this step")
    depends_on: list[int] = Field(
        default_factory=list,
        description="Step numbers this step must wait for before executing"
    )

class ExecutionPlan(BaseModel):
    steps: list[PlanStep] = Field(description="Dependency-ordered execution steps")

class SummaryOutput(BaseModel):
    topic: str
    bullets: list[str] = Field(description="5-7 crisp insight bullets for a LinkedIn audience")

class LinkedInPost(BaseModel):
    headline: str = Field(description="Punchy one-liner opening hook — never start with 'I'")
    body: str = Field(description="200-280 word post body, short paragraphs, line breaks for readability")
    hashtags: list[str] = Field(description="5 relevant hashtags, no # prefix")
    call_to_action: str = Field(description="Engaging closing question or CTA")

