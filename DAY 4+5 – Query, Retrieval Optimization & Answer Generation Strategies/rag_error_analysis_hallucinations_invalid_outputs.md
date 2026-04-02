# RAG Output Error Analysis


## Part 1 — Hallucination Examples

**Definition used:**
A hallucination occurs when the answer deviates from the ground truth by introducing unsupported information, omitting critical required details, or replacing precise terminology with vague descriptions.

| QID | Hallucination Type            | Brief Explanation                                                                                                    | Root Cause         |
| --- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Q2  | Missing critical entity       | The answer identified the categories but did not explicitly name the required component "Ancestral Trace Challenge." | Summarization bias |
| Q11 | Metric misidentification      | The answer described a scoring approach but failed to name the specific metric "Exact Match (EM)."                   | Term abstraction   |
| Q21 | Missing quantitative evidence | The explanation correctly mentioned data contamination but omitted key experimental statistics (90% vs 50–80% drop). | Evidence omission  |
| Q15 | Under-specified answer        | The answer stated the repetition count but omitted that averages were reported for stability.                        | Answer truncation  |
| Q17 | Conceptual simplification     | The explanation covered only one reason (focus on key points) and ignored the comparison to information-dense tasks. | Partial reasoning  |

---

### Hallucination Summary

* Total questions evaluated: **25**
* Hallucination cases identified: **5**
* Most common cause: **missing required details rather than fabricated facts**

---

## Part 2 — Invalid Output Examples

**Definition used:**
An invalid output occurs when the response violates the required JSON schema or formatting standards, even if the answer content is correct.

| QID | Failure Type                 | Brief Explanation                                                               | Severity | Root Cause                 |
| --- | ---------------------------- | ------------------------------------------------------------------------------- | -------- | -------------------------- |
| Q8  | Invalid JSON structure       | Citation stored as a key-value pair inside an array instead of a string.        | High     | Serialization error        |
| Q8  | Invalid citation format      | Section and page stored as structured fields rather than a single string entry. | Medium   | Incorrect formatting logic |
| Q6  | Duplicate citation           | The same citation entry appeared twice in the list.                             | Low      | Duplicate retrieval result |
| Q12 | Non-standard citation format | Citations used inconsistent labeling format (page/section separately).          | Low      | Template inconsistency     |
| Q4  | Incorrect citation mapping   | Citation referenced the wrong section relative to the ground truth.             | Medium   | Retrieval ranking mismatch |

---

### Invalid Output Summary

* Total invalid outputs identified: **5**
* Most severe issue: **invalid JSON structure**
* Most common issue: **citation formatting inconsistency**

---

## Key Observations

1. Most hallucinations were **omissions**, not fabricated information.
2. Structural formatting issues occurred even when answers were factually correct.
3. Citation generation is reliable but occasionally inconsistent in formatting.
4. The system demonstrates strong semantic performance but requires stricter output validation.

---

## Recommended Improvements

* Enforce strict JSON serialization validation before output.
* Standardize citation formatting templates.
* Add post-generation validation for required key terms.
* Use similarity thresholds together with semantic checks rather than alone.

---

## Final Metrics

| Metric                      | Value |
| --------------------------- | ----- |
| Total Questions             | 25    |
| Hallucination Cases         | 5     |
| Invalid Output Cases        | 5     |
| JSON Validity Rate          | 96%   |
| Semantic Accuracy (approx.) | ~92%  |

---

This format is suitable for inclusion in:

* RAG system evaluation reports
* Research papers
* Model benchmarking documentation
* Retrieval and generation error analysis sections
