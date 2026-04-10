import json
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from groq import Groq


@dataclass
class Turn:
    """A single conversation turn stored in memory."""
    user: str
    assistant: str
    tools_used: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    success: bool
    content: str
    tool_name: str

class ToolRegistry:
    """
    Centralized registry for tools.
    Each tool has:
      - a callable handler
      - a JSON schema (sent to the LLM)
      - an optional validator
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        handler: Callable,
        schema: dict,
        validator: Optional[Callable] = None,
    ):
        self._tools[name] = {
            "handler": handler,
            "schema": schema,
            "validator": validator,
        }

    def get_schemas(self) -> list[dict]:
        """Return tool schemas for the LLM API call."""
        return [t["schema"] for t in self._tools.values()]

    def execute(self, name: str, args: dict) -> ToolResult:
        if name not in self._tools:
            return ToolResult(success=False, content=f"Unknown tool: {name}", tool_name=name)

        entry = self._tools[name]

        # Validate first
        if entry["validator"]:
            try:
                entry["validator"](args)
            except ValueError as e:
                return ToolResult(success=False, content=str(e), tool_name=name)

        # Execute
        try:
            result = entry["handler"](**args)
            return ToolResult(success=True, content=result, tool_name=name)
        except Exception as e:
            return ToolResult(success=False, content=f"Execution error: {e}", tool_name=name)

class MemoryManager:
    """
    Lightweight turn-level memory.

    Stores up to `max_turns` full turns, then keeps a
    rolling plain-text summary so the agent remembers
    context without blowing up the context window.
    """

    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self._turns: list[Turn] = []
        self.summary: str = ""

    def add_turn(self, turn: Turn):
        self._turns.append(turn)
        if len(self._turns) > self.max_turns:
            # Compress oldest turn into summary
            oldest = self._turns.pop(0)
            self._update_summary(oldest)

    def _update_summary(self, turn: Turn):
        tools_note = f" [tools: {', '.join(turn.tools_used)}]" if turn.tools_used else ""
        self.summary = (
            (self.summary + "\n" if self.summary else "")
            + f"User asked: {turn.user[:120]}{tools_note}\n"
            + f"Assistant answered: {turn.assistant[:200]}"
        ).strip()

    def get_context_block(self) -> str:
        """Format memory as a system-level context block."""
        parts = []

        if self.summary:
            parts.append(f"[Conversation Summary]\n{self.summary}")

        if self._turns:
            recent = "\n".join(
                f"User: {t.user}\nAssistant: {t.assistant}"
                for t in self._turns[-3:]   # last 3 turns in full
            )
            parts.append(f"[Recent Turns]\n{recent}")

        return "\n\n".join(parts) if parts else ""

    @property
    def turn_count(self) -> int:
        return len(self._turns)

class ReActLoop:
    """
    Implements the ReAct (Reason → Act → Observe) cycle.

    Each iteration:
      1. REASON  — LLM decides what to do next
      2. ACT     — execute a tool (if needed)
      3. OBSERVE — append result to message history
      4. REPEAT  — until no more tool calls, or max_steps reached
    """

    MAX_STEPS = 6

    def __init__(self, client: Groq, model: str, tool_registry: ToolRegistry):
        self.client = client
        self.model = model
        self.tools = tool_registry

    def run(self, messages: list[dict]) -> tuple[str, list[str]]:
        """
        Run the ReAct loop.

        Returns:
            (final_answer: str, tools_used: list[str])
        """
        tools_used: list[str] = []

        for step in range(self.MAX_STEPS):
            # ── REASON: ask LLM what to do ──────────────────
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools.get_schemas(),
                tool_choice="auto",
            )

            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            # ── ACT + OBSERVE (if tool call) ─────────────────
            if tool_calls:
                messages.append(msg)

                for call in tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)

                    print(f"  [ReAct step {step+1}] ACT → {name}({args})")

                    result = self.tools.execute(name, args)
                    tools_used.append(name)

                    if not result.success:
                        # Feed error back so LLM can self-correct
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": name,
                            "content": json.dumps({"error": result.content}),
                        })
                        print(f"  [ReAct step {step+1}] OBSERVE → error: {result.content}")
                    else:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": name,
                            "content": result.content,
                        })
                        print(f"  [ReAct step {step+1}] OBSERVE → ok")

            else:
                # ── STOP: LLM gave a final answer ───────────
                print(f"  [ReAct step {step+1}] STOP → final answer produced")
                return msg.content or "", tools_used

        # Safety net: force a final answer if we hit MAX_STEPS
        messages.append({
            "role": "user",
            "content": "Please provide your final answer based on what you've gathered so far.",
        })
        final = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tool_choice="none",
        )
        return final.choices[0].message.content or "", tools_used

DOCUMENTS = [
    {"id": 1, "city": "lahore",    "category": "food", "text": "Best biryani spots in Lahore"},
    {"id": 2, "city": "karachi",   "category": "tech", "text": "Top startups in Karachi"},
    {"id": 3, "city": "islamabad", "category": "food", "text": "Fine dining in Islamabad"},
    {"id": 4, "city": "lahore",    "category": "tech", "text": "Software houses in Lahore"},
    {"id": 5, "city": "karachi",   "category": "food", "text": "Street food gems in Karachi"},
    {"id": 6, "city": "islamabad", "category": "tech", "text": "IT parks and coworking spaces in Islamabad"},
]


def _calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return json.dumps({"result": result})
    except Exception:
        return json.dumps({"error": "Invalid expression"})


def _validate_calculate(args: dict):
    if "expression" not in args:
        raise ValueError("Missing 'expression'")
    if not isinstance(args["expression"], str):
        raise ValueError("'expression' must be a string")


def _retrieve_documents(city: str = None, category: str = None) -> str:
    results = DOCUMENTS
    if city:
        results = [d for d in results if d["city"] == city.lower()]
    if category:
        results = [d for d in results if d["category"] == category.lower()]
    return json.dumps({"results": results, "count": len(results)})


def _validate_retrieve(args: dict):
    allowed = {"city", "category"}
    for key in args:
        if key not in allowed:
            raise ValueError(f"Invalid field: '{key}'. Allowed: city, category")
    if not any(k in args for k in allowed):
        raise ValueError("Provide at least one of: city, category")

class RAGAgent:
    """
    Class-based RAG Agent with:
      - ToolRegistry  (pluggable tools)
      - MemoryManager (rolling summary + recent turns)
      - ReActLoop     (reason → act → observe)
      - Multi-turn support
    """

    MODEL = "openai/gpt-oss-120b"

    SYSTEM_PROMPT = textwrap.dedent("""
        You are a smart assistant with access to tools and memory of prior conversation.

        ## Decision framework (follow in order):
        1. REFUSE   — if the request is harmful or outside your scope, say so clearly.
        2. RETRIEVE — if the user asks about cities, categories, food, or tech documents, use retrieve_documents.
        3. CALCULATE — if the user needs a math result, use calculate.
        4. ANSWER   — if no tool is needed, answer directly from knowledge and memory.

        ## Tool rules:
        - retrieve_documents accepts ONLY: city (string), category (string).
        - DO NOT invent parameters like 'query' or 'filter'.
        - calculate accepts only a math expression string.

        ## ReAct format (think step by step):
        Thought: [your reasoning]
        Action: [tool name or "answer"]
        Observation: [result of action]
        ... repeat if needed ...
        Final Answer: [your response to the user]

        Use memory context when provided — refer to prior turns naturally.
    """).strip()

    def __init__(self):
        self.client = Groq()
        self.memory = MemoryManager(max_turns=5)
        self.tools = ToolRegistry()
        self.react = ReActLoop(self.client, self.MODEL, self.tools)
        self._register_default_tools()

    def _register_default_tools(self):
        self.tools.register(
            name="calculate",
            handler=_calculate,
            validator=_validate_calculate,
            schema={
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Evaluate a mathematical expression and return the result.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "A valid Python math expression, e.g. '2 ** 10 + 5'",
                            }
                        },
                        "required": ["expression"],
                    },
                },
            },
        )

        self.tools.register(
            name="retrieve_documents",
            handler=_retrieve_documents,
            validator=_validate_retrieve,
            schema={
                "type": "function",
                "function": {
                    "name": "retrieve_documents",
                    "description": (
                        "Filter documents by city and/or category. "
                        "Available cities: lahore, karachi, islamabad. "
                        "Available categories: food, tech."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name (lahore / karachi / islamabad)",
                            },
                            "category": {
                                "type": "string",
                                "description": "Category (food / tech)",
                            },
                        },
                    },
                },
            },
        )

    def _build_messages(self, user_input: str) -> list[dict]:
        """Assemble the message list: system + memory context + current user turn."""
        system_content = self.SYSTEM_PROMPT
        memory_ctx = self.memory.get_context_block()
        if memory_ctx:
            system_content += f"\n\n## Memory\n{memory_ctx}"

        return [
            {"role": "system", "content": system_content},
            {"role": "user",   "content": user_input},
        ]

    def chat(self, user_input: str) -> str:
        """
        Process one user turn through the full ReAct agent loop.
        Updates memory after each turn.
        """
        print(f"\n")
        print(f"USER: {user_input}")
        print(f"\n")

        messages = self._build_messages(user_input)
        answer, tools_used = self.react.run(messages)

        # Persist this turn into memory
        self.memory.add_turn(Turn(
            user=user_input,
            assistant=answer,
            tools_used=tools_used,
        ))

        print(f"\nASSISTANT: {answer}")
        return answer

    def reset_memory(self):
        """Clear all memory (start fresh conversation)."""
        self.memory = MemoryManager(max_turns=5)
        print("[Memory cleared]")


def run_multiturn_test():
    """
    Test suite for multi-turn context-dependent queries.
    Each query deliberately builds on the previous one.
    """
    agent = RAGAgent()

    test_turns = [

        "What food places do you have in Lahore?",

        "What about tech stuff in the same city?",

        "If I visit 3 places a day, how many days to visit all 6 documents?",

        "And how many in Islamabad?",

        "Compare that to Karachi — what options exist there?",

        "List all food the document titles you retrieved earlier in our conversation."
    ]

    print("\n")
    print("RAGAgent Multi-Turn Test — ReAct + Memory")
    print("\n")

    for i, query in enumerate(test_turns, 1):
        print(f"\n[Turn {i}/{len(test_turns)}]")
        agent.chat(query)

    print("\n")
    print("Test complete.")
    print("\n")


if __name__ == "__main__":
    run_multiturn_test()