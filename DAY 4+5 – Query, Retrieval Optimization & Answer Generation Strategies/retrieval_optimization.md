# Vector vs Hybrid Retrieval Comparison

```
PDF: Around 30+ pages research paper
Questions: 25
Top-K Retrieved: 5
```

| Retrieval Strategy | Hits | Total | Hit-Rate@5 |
| ------------------ | ---- | ----- | ---------- |
| Vector Retrieval   | 17   | 25    | 0.68       |
| Hybrid Retrieval   | 20   | 25    | 0.80       |


### Key Interpretation

```
Hybrid retrieval:

Hybrid retrieval improved recall by 3 questions (Hit-Rate@5 from 0.68 → 0.80).
```


## 5 Examples Where Hybrid Retrieval Improved Similarity

| Question                                                                      | Vector Status / Similarity | Hybrid Status / Similarity | Improvement Notes                                    |
| ----------------------------------------------------------------------------- | -------------------------- | -------------------------- | ---------------------------------------------------- |
| What problem does NeedleBench aim to address in evaluating long-context LLMs? | PASS, 0.7100               | PASS, 0.7386               | Similarity increased by +0.0286                      |
| What is the name of the information-dense task proposed in the paper?         | PASS, 0.7900               | PASS, 0.8031               | Similarity increased +0.0131                         |
| What capability is tested by the Multi-Needle Reasoning task?                 | PASS, 0.9100               | PASS, 0.9359               | Large similarity boost +0.0259                       |
| Why do information-dense tasks provide a more realistic evaluation?           | FAIL, 0.7100               | PASS, 0.7876               | Status improved from FAIL → PASS, similarity +0.0776 |
| How many repetitions are used to stabilize results?                           | FAIL, 0.6900               | PASS, 0.7087               | Status improved FAIL → PASS, similarity +0.0187      |


## Citation Evaluation Table (All Questions)

| Q#  | Expected Section (Page)         | Answer Citation      | Verdict | Notes                  |
| --- | ------------------------------- | -------------------- | ------- | ---------------------- |
| Q1  | Abstract (1)                    | 🚫 Missing           | 🚫      | No citation            |
| Q2  | 3 Tasks and Datasets (3)        | section 3, page 3    | ⚠️      | Section too coarse     |
| Q3  | 4.2 NeedleBench Info-Dense (11) | 🚫 Missing           | 🚫      | No citation            |
| Q4  | 3.2 Info-Dense Tasks (5)        | section 4.2, page 12 | ❌       | Wrong section          |
| Q5  | 1 Introduction (2)              | 🚫 Missing           | 🚫      | No citation            |
| Q6  | 3.1 Info-Sparse Tasks (3)       | 3.1, page 3          | ✅       | Correct                |
| Q7  | 3.1 Info-Sparse Tasks (3)       | G, page 23           | ❌       | Completely wrong       |
| Q8  | 3.1 Info-Sparse Tasks (3)       | 3.1, page 4          | ⚠️      | Page slightly off      |
| Q9  | 3 Tasks and Datasets (4)        | 3.1, page 4          | ⚠️      | Subsection mismatch    |
| Q10 | 3 Tasks and Datasets (4)        | 🚫 Missing           | 🚫      | No citation            |
| Q11 | 3 Tasks and Datasets (4)        | 🚫 Missing           | 🚫      | No citation            |
| Q12 | 3 Tasks and Datasets (5)        | 🚫 Missing           | 🚫      | No citation            |
| Q13 | 3.2 Info-Dense Tasks (6)        | 🚫 Missing           | 🚫      | No citation            |
| Q14 | 3.2 Info-Dense Tasks (6)        | section 4, page 6    | ❌       | Wrong section          |
| Q15 | 3 Tasks and Datasets (5)        | 3.2, page 5          | ⚠️      | Close but wrong        |
| Q16 | 3.2 Info-Dense Tasks (5)        | 🚫 Missing           | 🚫      | No citation            |
| Q17 | 1 Introduction (2)              | section 1, page 2    | ✅       | Correct                |
| Q18 | 2 Related Work (3)              | 🚫 Missing           | 🚫      | No citation            |
| Q19 | 4.1.1 Retrieval Perf (6)        | 🚫 Missing           | 🚫      | No citation            |
| Q20 | 4.1.3 Model Scale (8)           | 4.1.3, page 8        | ✅       | Correct                |
| Q21 | Appendix D (19)                 | multiple (2, 3.1, D) | ⚠️      | One correct (D), noisy |
| Q22 | 4.1.4 Needle Count (9)          | 4.2, page 11         | ❌       | Wrong section          |
| Q23 | 3 Tasks and Datasets (5)        | 3.2, page 5          | ⚠️      | Close but wrong        |
| Q24 | 3.2 Info-Dense Tasks (5)        | 3.2, page 5          | ✅       | Correct                |
| Q25 | 4.1.3 Model Scale (9)           | 4.1.4, page 9        | ⚠️      | Neighbor section       |


## Answer Evaluation Table (All Questions)

| Question | Similarity Unranked | Similarity Ranked | Correct Unranked | Correct Ranked | Status Unranked | Status Ranked |
| -------- | ------------------- | ----------------- | ---------------- | -------------- | --------------- | ------------- |
| Q1       | 0.7386              | 0.8892            | ✅                | ✅              | PASS            | PASS          |
| Q2       | 0.6501              | 0.5513            | ❌                | ❌              | FAIL            | FAIL          |
| Q3       | 0.7159              | 0.5513            | ✅                | ❌              | PASS            | FAIL          |
| Q4       | 0.8031              | 0.8206            | ✅                | ✅              | PASS            | PASS          |
| Q5       | 0.8207              | 0.7793            | ✅                | ✅              | PASS            | PASS          |
| Q6       | 0.8807              | 0.9438            | ✅                | ✅              | PASS            | PASS          |
| Q7       | 0.7486              | 0.7507            | ✅                | ✅              | PASS            | PASS          |
| Q8       | 0.9359              | 0.8368            | ✅                | ✅              | PASS            | PASS          |
| Q9       | 0.8139              | 0.7967            | ✅                | ✅              | PASS            | PASS          |
| Q10      | 0.7430              | 0.7927            | ✅                | ✅              | PASS            | PASS          |
| Q11      | 0.8225              | 0.8204            | ✅                | ✅              | PASS            | PASS          |
| Q12      | 0.9048              | 0.9230            | ✅                | ✅              | PASS            | PASS          |
| Q13      | 0.8474              | 0.8368            | ✅                | ✅              | PASS            | PASS          |
| Q14      | 0.8008              | 0.7791            | ✅                | ✅              | PASS            | PASS          |
| Q15      | 0.7087              | 0.7927            | ✅                | ✅              | PASS            | PASS          |
| Q16      | 0.7876              | 0.8368            | ✅                | ✅              | PASS            | PASS          |
| Q17      | 0.8945              | 0.9220            | ✅                | ✅              | PASS            | PASS          |
| Q18      | 0.7807              | 0.8368            | ✅                | ✅              | PASS            | PASS          |
| Q19      | 0.8443              | 0.8443            | ✅                | ✅              | PASS            | PASS          |
| Q20      | 0.8463              | 0.8368            | ✅                | ✅              | PASS            | PASS          |
| Q21      | 0.6722              | 0.7300            | ❌                | ❌              | FAIL            | FAIL          |
| Q22      | 0.7400              | 0.8368            | ✅                | ✅              | PASS            | PASS          |
| Q23      | 0.9494              | 0.9550            | ✅                | ✅              | PASS            | PASS          |
| Q24      | 0.6370              | 0.6368            | ❌                | ❌              | FAIL            | FAIL          |
| Q25      | 0.6858              | 0.7300            | ❌                | ❌              | FAIL            | FAIL          |
