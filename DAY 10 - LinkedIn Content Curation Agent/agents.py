import base64
import json
import logging
import os
from urllib.parse import quote

import httpx

from prompts import _EDITOR_PROMPT, _GENERATOR_PROMPT, _PLANNER_PROMPT
from models import ExecutionPlan, LinkedInPost
from llm import make_llm

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agents")

class PlannerAgent:
    """LCEL chain: prompt | groq.with_structured_output(ExecutionPlan)"""

    def __init__(self):
        llm = make_llm(temperature=0.1)
        self.chain = _PLANNER_PROMPT | llm.with_structured_output(ExecutionPlan)

    async def plan(self, topic: str, audience: str, tone: str) -> ExecutionPlan:
        logger.debug("PlannerAgent.plan | topic=%r audience=%r tone=%r", topic, audience, tone)
        result = await self.chain.ainvoke(
            {"topic": topic, "audience": audience, "tone": tone}
        )
        logger.debug("PlannerAgent.plan | steps=%s", [s.tool for s in result.steps])
        return result

class GeneratorAgent:
    """LCEL chain: prompt | groq.with_structured_output(LinkedInPost)"""

    def __init__(self):
        self.chain = _GENERATOR_PROMPT | make_llm(0.75).with_structured_output(LinkedInPost, method="json_mode")

    async def generate(self, topic: str, audience: str, tone: str, research: str) -> LinkedInPost:
        logger.debug("GeneratorAgent.generate | topic=%r audience=%r", topic, audience)
        result = await self.chain.ainvoke(
            {"topic": topic, "audience": audience, "tone": tone, "research": research}
        )
        logger.debug("GeneratorAgent.generate | headline=%r", result.headline[:60])
        return result

class EditorAgent:
    """LCEL: prompt | groq.with_structured_output(LinkedInPost), falls back to original on failure."""

    def __init__(self):
        self.chain = _EDITOR_PROMPT | make_llm(0.3).with_structured_output(LinkedInPost, method="json_mode")

    async def edit(self, post: LinkedInPost) -> LinkedInPost:
        logger.debug("EditorAgent.edit | input_headline=%r", post.headline[:60])
        try:
            result = await self.chain.ainvoke(
                {"draft": json.dumps(post.model_dump(), indent=2)}
            )
            logger.debug("EditorAgent.edit | output_headline=%r", result.headline[:60])
            return result
        except Exception as exc:
            logger.warning("EditorAgent.edit | structured output failed, returning original: %s", exc)
            return post  # graceful degradation

class ImageGeneratorAgent:
    async def generate(self, topic: str, headline: str) -> tuple[str | None, str | None]:
        prompt = (
            f"Professional LinkedIn banner illustration for: {headline or topic}. "
            "Modern corporate aesthetic, bold abstract geometry, "
            "dark navy and electric blue palette. No text, no people, high resolution."
        )
        url = (
            f"https://gen.pollinations.ai/image/{quote(topic)}"
            f"?model=flux&width=512&height=512&seed=0&enhance=false&key={os.getenv('POLLINATIONS_API_KEY')}"
        )
        logger.debug("ImageGeneratorAgent.generate | topic=%r headline=%r", topic, headline[:60] if headline else "")
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                r = await client.get(url, follow_redirects=True)
                logger.debug("ImageGeneratorAgent.generate | status=%s content-type=%s size=%d",
                             r.status_code, r.headers.get("content-type"), len(r.content))
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    return None, base64.b64encode(r.content).decode()
        except Exception as exc:
            logger.warning("ImageGeneratorAgent.generate | failed: %s", exc)
        return None, None
