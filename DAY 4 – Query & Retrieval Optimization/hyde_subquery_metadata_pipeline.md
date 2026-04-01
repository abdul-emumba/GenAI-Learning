Here’s a diagram showing how HyDE, sub-query decomposition, and metadata-aware retrieval interact in a pipeline:

```
                    +-----------------+
                    |   User Query Q   |
                    +--------+--------+
                             |
        +--------------------+--------------------+
        |                                         |
+-------v-------+                         +-------v-----------------+
|  HyDE Module  |                         | Sub-query De-           |
| (Hypothetical |                         | composition             |
|   Embedding)  |                         | (Split Q → q1, q2, ...) |
+-------+-------+                         +-------+-----------------+
        |                                         |
        +--------------------+--------------------+
                             |
                  +----------v-----------+
                  | Candidate Document   |
                  | Retrieval (Vector DB)|
                  +----------+-----------+
                             |
                     +-------v--------+
                     | Metadata Filter|
                     | (date, source, |
                     |  category, etc)|
                     +-------+--------+
                             |
                     +-------v--------+
                     |  Ranked Results |
                     |  (Top-k Docs)   |
                     +----------------+
```


## Explanation:

HyDE generates a hypothetical answer embedding from the query to guide semantic retrieval.
Sub-query decomposition breaks complex queries into smaller pieces for more thorough coverage.
Vector DB retrieves candidate documents based on embeddings.
Metadata filter reduces irrelevant candidates using structured metadata.
Ranking produces the final top-k documents for downstream tasks (like LLM QA).