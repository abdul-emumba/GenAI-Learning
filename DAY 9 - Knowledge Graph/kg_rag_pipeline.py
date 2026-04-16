import os
import dotenv

from langchain_neo4j import Neo4jGraph, Neo4jVector, GraphCypherQAChain
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from groq import Groq
from typing import Any, List, Optional

dotenv.load_dotenv()

NEO4J_URI      = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    refresh_schema=False,
)
print("Connected to Neo4j")

DATASET_URL = (
    "https://raw.githubusercontent.com/dcarpintero/"
    "generative-ai-101/main/dataset/synthetic_articles.csv"
)

q_load_articles = f"""
    LOAD CSV WITH HEADERS
    FROM '{DATASET_URL}'
    AS row
    FIELDTERMINATOR ';'
    MERGE (a:Article {{title: row.Title}})
    SET a.abstract          = row.Abstract,
        a.publication_date  = date(row.Publication_Date)
    FOREACH (researcher IN split(row.Authors, ',') |
        MERGE (p:Researcher {{name: trim(researcher)}})
        MERGE (p)-[:PUBLISHED]->(a))
    FOREACH (topic IN [row.Topic] |
        MERGE (t:Topic {{name: trim(topic)}})
        MERGE (a)-[:IN_TOPIC]->(t))
"""

graph.query(q_load_articles)
print("Dataset loaded into Neo4j graph")

try:
    graph.refresh_schema()
    print("\n📐 Graph Schema:")
    print(graph.get_schema)
except Exception:
    print("\n📐 Graph Schema: (skipped — APOC plugin not available)")

# Build vector index on Article nodes
vector_index = Neo4jVector.from_existing_graph(
    HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    index_name="articles",
    node_label="Article",
    text_node_properties=["topic", "title", "abstract"],
    embedding_node_property="embedding",
)
print("\nVector index built on Article nodes")

# Custom LLM wrapper for Groq
class GroqLLM(LLM):
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0

    @property
    def _llm_type(self) -> str:
        return "groq"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs) -> str:
        client = Groq()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content

# Set up retrieval chain for vector search (LCEL replacement for RetrievalQA)
_rag_prompt = PromptTemplate.from_template(
    "Use the following context to answer the question.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)
_llm = GroqLLM()
vector_qa = (
    {
        "context": vector_index.as_retriever() | (lambda docs: "\n\n".join(d.page_content for d in docs)),
        "question": RunnablePassthrough(),
    }
    | _rag_prompt
    | _llm
    | StrOutputParser()
)

def similarity_search(query: str) -> str:
    """Run a semantic similarity search over articles."""
    return vector_qa.invoke(query)

try:
    graph.refresh_schema()
except Exception:
    pass

# Set up GraphCypherQAChain to translate natural language queries into Cypher and execute them
cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=GroqLLM(temperature=0),
    qa_llm=GroqLLM(temperature=0),
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
)

def graph_query(query: str) -> str:
    """Translate a natural language query to Cypher and run it."""
    result = cypher_chain.invoke({"query": query})
    return result.get("result", str(result))

if __name__ == "__main__":

    print("\n" + "═" * 60)
    print("  RAG PIPELINE")
    print("═" * 60)

    # ── Vector / similarity queries ──────────────
    print("\n[VECTOR SEARCH] Which articles discuss AI's impact on daily life?")
    answer = similarity_search(
        "which articles discuss how AI might affect our daily life? "
        "include the article titles and abstracts."
    )
    print(answer)

    # ── Graph traversal queries ──────────────────
    print("\n[GRAPH QUERY] How many articles has Emily Chen published?")
    print(graph_query("How many articles has published Emily Chen?"))

    print("\n[GRAPH QUERY] Researcher pairs with more than 3 joint articles?")
    print(graph_query(
        "Are there any pair of researchers who have published "
        "more than three articles together?"
    ))

    print("\n[GRAPH QUERY] Who collaborated with the most peers?")
    print(graph_query("Which researcher has collaborated with the most peers?"))

    # ── Interactive REPL ─────────────────────────
    print("\n" + "═" * 60)
    print("  INTERACTIVE MODE  (type 'exit' to quit)")
    print("  Prefix query with  'v:'  for vector search")
    print("  Prefix query with  'g:'  for graph traversal")
    print("═" * 60)

    while True:
        try:
            user_input = input("\nQuery> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input or user_input.lower() == "exit":
            print("Bye!")
            break

        if user_input.startswith("v:"):
            q = user_input[2:].strip()
            print("\n[Vector Search Result]")
            print(similarity_search(q))
        elif user_input.startswith("g:"):
            q = user_input[2:].strip()
            print("\n[Graph Query Result]")
            print(graph_query(q))
        else:
            # Default: try graph query
            print("\n[Graph Query Result]  (prefix with 'v:' for vector search)")
            print(graph_query(user_input))