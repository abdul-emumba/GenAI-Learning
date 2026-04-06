
# Preference-Aware Travel RAG Assistant

This is a **Retrieval-Augmented Generation (RAG)** system designed to provide travel recommendations based on user preferences such as city, interests, and budget. It integrates web content ingestion, document chunking, vector retrieval, reranking, context judgment, and LLM-based answer generation.

---

## Embedding Choice

We use **`sentence-transformers/all-MiniLM-L6-v2`**:

- Small, efficient model optimized for **semantic similarity**.
- Good tradeoff between **accuracy and speed**.
- Converts text chunks and queries into dense vectors for **vector similarity search**.

---

## Vector Database Choice

We use **ChromaDB** via LangChain’s `Chroma` vectorstore:

- Lightweight and easy to set up for small datasets
- Persistent storage: chunks and metadata are saved to disk
- Built-in metadata filtering (city, price, category)
- Fast similarity search with embeddings
- Simple Python API, no external server needed
- Supports future scaling to multiple collections or larger datasets

---

## One Failure Case Observed

* **Issue:** Queries sometimes return **context_insufficient**, even when documents exist.
* **Cause:** Overly strict metadata filters or low similarity scores can prevent retrieval of relevant documents.
* **Impact:** Users see a message like:

```
"The retrieved information is insufficient to answer your query accurately. Please try rephrasing your question or providing more details."
```

