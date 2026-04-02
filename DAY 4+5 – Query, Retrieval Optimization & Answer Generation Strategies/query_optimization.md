# Query Optimization Comparison

```
PDF: Around 30+ pages research paper
Questions: 25
Top-K Retrieved: 5
```

## Hit Rate@5 Comparison
| Method          | Correct (Hits) | Total | Hit-Rate@5 |
| --------------- | -------------- | ----- | ---------- |
| Baseline        | 15             | 25    | **0.60**   |
| HyDE            | 12             | 25    | **0.48**   |
| Multi-Retrieval | 17             | 25    | **0.68**   |

### Insight:

- Multi-retrieval is best (+8% over baseline)
- HyDE underperforms baseline overall (likely due to noisy hypothetical answers)

## Failure Analysis by Method (Retrieval vs Generation)
### Classification Summary per Method

| Method              | Retrieval Failures | Generation Failures | Total Failures | Accuracy         |
| ------------------- | ------------------ | ------------------- | -------------- | ---------------- |
| **Baseline**        | 7                  | 3                   | 10             | **15/25 (0.60)** |
| **HyDE**            | 8                  | 5                   | 13             | **12/25 (0.48)** |
| **Multi-Retrieval** | 5                  | 3                   | 8              | **17/25 (0.68)** |

### Insights
- Baseline: More retrieval issues → weak recall
- HyDE: Highest failures → adds generation noise + retrieval drift
- Multi: Best overall → reduces retrieval failures significantly

## Examples Where Query Optimization Improved Results
| Question                               | Baseline | HyDE | Multi | Failure Type Fixed   | Why It Improved             |
| -------------------------------------- | -------- | ---- | ----- | -------------------- | --------------------------- |
| Premature reasoning (“under-thinking”) | ❌        | ✅    | ✅     | Generation → Fixed   | Better keyword retrieval    |
| Scoring metric (Exact Match)           | ❌        | ✅    | ✅     | Generation → Fixed   | Reduced over-complication   |
| ENL-50 metric                          | ❌        | ❌    | ✅     | Retrieval → Fixed    | Multi-query improved recall |
| ENL-50 threshold                       | ❌        | ✅    | ✅     | Retrieval → Fixed    | Numeric fact retrieved      |
| Context length support                 | ⚠️       | ❌    | ✅     | Retrieval → Improved | Better coverage of values   |

## Failure Cases (Optimization Did NOT Help)
| Question                          | Baseline | HyDE | Multi | Failure Type | Root Cause                  |
| --------------------------------- | -------- | ---- | ----- | ------------ | --------------------------- |
| Task categories (NeedleBench)     | ❌        | ❌    | ❌     | Generation   | Concept confusion           |
| Information-dense task name (ATC) | ❌        | ❌    | ❌     | Retrieval    | Missing exact entity        |
| Needle data type (synthetic)      | ❌        | ❌    | ❌     | Generation   | Generic answer              |
| Experiment repetitions (R=10)     | ❌        | ❌    | ❌     | Retrieval    | Fine-grained detail missing |
| Info-dense vs sparse reasoning    | ❌        | ❌    | ❌     | Generation   | Misaligned explanation      |
