from langchain_groq import ChatGroq

# LLM configuration across agents, with fallback
def make_llm(temperature: float = 0.7) -> ChatGroq:
    primary = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        max_tokens=2048,
    )
    fallback = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=temperature,
        max_tokens=2048,
    )
    return primary.with_fallbacks([fallback])

