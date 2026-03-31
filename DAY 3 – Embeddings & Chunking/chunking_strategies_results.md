# Chunking Strategies Comparison
```
PDF: Around 30+ pages research paper
Evaluation Method: Semantic Retrieval using embeddings + multiple chunking strategies
Questions: 25
Top-K Retrieved: 5
```

## Hit Rate@5 Comparison

| Chunking Strategy | Hit Rate@5 |
| ----------------- | ---------- |
| Fixed             | 0.08       |
| Overlap           | 0.08       |
| Recursive         | 0.24       |
| Sentence          | 0.24       |

### Observation:
Advanced chunking strategies like Recursive and Sentence-based chunking significantly improve the hit rate compared to simpler Fixed or Overlap chunking. This is likely because larger and semantically coherent chunks help embeddings capture more context for retrieval.

## Per-Question Comparison

| Question | Fixed | Overlap | Recursive | Sentence |
| -------- | ----- | ------- | --------- | -------- |
| Q1       | ✗     | ✗       | ✗         | ✗        |
| Q2       | ✗     | ✗       | ✗         | ✗        |
| Q3       | ✗     | ✗       | ✓         | ✓        |
| Q4       | ✗     | ✗       | ✗         | ✗        |
| Q5       | ✗     | ✗       | ✗         | ✗        |
| Q6       | ✗     | ✗       | ✗         | ✗        |
| Q7       | ✓     | ✓       | ✗         | ✗        |
| Q8       | ✗     | ✗       | ✓         | ✓        |
| Q9       | ✗     | ✗       | ✗         | ✗        |
| Q10      | ✗     | ✗       | ✗         | ✗        |
| Q11      | ✓     | ✓       | ✗         | ✗        |
| Q12      | ✗     | ✗       | ✗         | ✗        |
| Q13      | ✗     | ✗       | ✗         | ✗        |
| Q14      | ✗     | ✗       | ✓         | ✓        |
| Q15      | ✗     | ✗       | ✗         | ✗        |
| Q16      | ✗     | ✗       | ✗         | ✗        |
| Q17      | ✗     | ✗       | ✗         | ✗        |
| Q18      | ✗     | ✗       | ✗         | ✗        |
| Q19      | ✗     | ✗       | ✗         | ✗        |
| Q20      | ✗     | ✗       | ✓         | ✓        |
| Q21      | ✗     | ✗       | ✗         | ✗        |
| Q22      | ✗     | ✗       | ✓         | ✓        |
| Q23      | ✗     | ✗       | ✗         | ✗        |
| Q24      | ✗     | ✗       | ✓         | ✓        |
| Q25      | ✗     | ✗       | ✗         | ✗        |


### Observation:

Questions Q3, Q8, Q14, Q20, Q22, Q24 show improved retrieval with advanced chunking strategies.
Questions Q7 and Q11 were better retrieved with simpler chunking, possibly because splitting sentences or recursive chunks fragmented the key information.
Overall, semantic chunking strategies help especially for multi-step or reasoning-based questions where context is longer or spread across paragraphs.


### Cases where advanced chunking improved retrieval
Advanced Chunking (Recursive/Sentence) improved hit rate for:
```
Q3, Q8, Q14, Q20, Q22, Q24
```

### Cases where advanced chunking did not improved retrieval
Simpler Chunking performed better for:
```
Q7, Q11
```

#### Explanation:
```
- Recursive/Sentence chunking preserves semantic meaning and larger context, making embeddings more effective for reasoning or multi-part answers.
- Fixed/Overlap chunks may work better for short, specific answers where large context adds noise.
```