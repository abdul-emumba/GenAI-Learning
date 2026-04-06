 # High-Level Architecture
 ```
                ┌────────────────────┐
                │   Travel URLs      │
                │ (5–10 web pages)   │
                └─────────┬──────────┘
                          │
                          ▼
                ┌──────────────────-──┐
                │  Ingestion Pipeline │
                │  - Fetch HTML       │
                │  - Clean text       │
                │  - Chunk text       │
                │  - Add metadata     │
                └─────────┬────────-──┘
                          │
                          ▼
                ┌───────────────────--─┐
                │ Embedding Model      │
                │ sentence-transformers|
                └─────────┬────────--──┘
                          │
                          ▼
                ┌─────────────────-───┐
                │   Vector DB         │
                │     Chroma          │
                └─────────┬─────-─────┘
                          │
                          ▼
User Query ─────────────► Preference Extraction
                          │
                          ▼
                    Retrieval
              (semantic + metadata filter)
                          │
                          ▼
                     Re-ranking
                   (Score Based)
                          │
                          ▼
                Context Quality Check
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
     context_good                context_insufficient
            │                           │
            ▼                           ▼
     Generate Answer             refused to answer
            │
            ▼
         UI Output

```