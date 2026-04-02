# Answer Gnenration Strategies

```
PDF: Around 30+ pages research paper
Questions: 25
Top-K Retrieved: 5
```

## Answer Correctness Comparison Table

Criteria used

PASS: similarity ≥ 0.70 and semantically correct
PLAUSIBLE LOW: similarity < 0.70 but answer logically matches ground truth
FAIL: incorrect / incomplete / missing key concept

| QID | Similarity | Auto Status | Final Judgment    | Notes                                                  |
| --- | ---------- | ----------- | ----------------- | ------------------------------------------------------ |
| Q1  | 0.916      | PASS        | PASS              | Accurate and complete                                  |
| Q2  | 0.456      | FAIL        | FAIL              | Missing explicit naming of ATC as info-dense category  |
| Q3  | 0.752      | PASS        | PASS              | Correct definition                                     |
| Q4  | 0.735      | PASS        | PASS              | Exact match                                            |
| Q5  | 0.797      | PASS        | PASS              | Correct list                                           |
| Q6  | 0.935      | PASS        | PASS              | Correct capability                                     |
| Q7  | 0.817      | PASS        | PASS              | Correct capability                                     |
| Q8  | 0.924      | PASS        | PASS              | Correct reasoning description                          |
| Q9  | 0.708      | PASS        | PASS              | Above threshold                                        |
| Q10 | 0.482      | FAIL        | **PLAUSIBLE LOW** | Correct dataset but similarity low due to short answer |
| Q11 | 0.495      | FAIL        | FAIL              | Missing "Exact Match" metric explicitly                |
| Q12 | 0.810      | PASS        | PASS              | Correct condition                                      |
| Q13 | 0.792      | PASS        | PASS              | Correct metric                                         |
| Q14 | 0.706      | PASS        | PASS              | Correct threshold                                      |
| Q15 | 0.351      | FAIL        | **PLAUSIBLE LOW** | Correct value but wording minimal                      |
| Q16 | 0.717      | PASS        | PASS              | Correct reasoning                                      |
| Q17 | 0.700      | FAIL        | PASS              | Borderline threshold rounding issue                    |
| Q18 | 0.840      | PASS        | PASS              | Correct explanation                                    |
| Q19 | 0.891      | PASS        | PASS              | Accurate architecture reasoning                        |
| Q20 | 0.846      | PASS        | PASS              | Correct scaling explanation                            |
| Q21 | 0.666      | FAIL        | **PLAUSIBLE LOW** | Correct concept but missing quantitative evidence      |
| Q22 | 0.759      | PASS        | PASS              | Correct trend                                          |
| Q23 | 0.847      | PASS        | PASS              | Correct reasoning                                      |
| Q24 | 0.808      | PASS        | PASS              | Correct explanation                                    |
| Q25 | 0.788      | PASS        | PASS              | Correct limitation explanation                         |

### Correctness Summary

| Metric                       | Value  |
| ---------------------------- | ------ |
| Total Questions              | 25     |
| Strict PASS                  | **20** |
| Plausible but Low Similarity | **4**  |
| True Failures                | **3**  |


## Citation Presence and Correctness Table
Validation Rules

Citation considered correct if:

Section matches expected section
Page matches expected page
Reference logically exists

| QID | Citation Present | Correct Section | Correct Page | Final Citation Status | Issue                    |
| --- | ---------------- | --------------- | ------------ | --------------------- | ------------------------ |
| Q1  | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q2  | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q3  | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q4  | Yes              | No              | No           | FAIL                  | Wrong section reference  |
| Q5  | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q6  | Yes              | Yes             | Yes          | PASS                  | Duplicate citation       |
| Q7  | Yes              | Partial         | Partial      | WARNING               | Mixed sections           |
| Q8  | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q9  | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q10 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q11 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q12 | Yes              | Partial         | Partial      | WARNING               | Generic reference format |
| Q13 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q14 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q15 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q16 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q17 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q18 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q19 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q20 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q21 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q22 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q23 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q24 | Yes              | Yes             | Yes          | PASS                  | —                        |
| Q25 | Yes              | Yes             | Yes          | PASS                  | —                        |

### Citation Summary

| Metric                  | Value       |
| ----------------------- | ----------- |
| Citation Present Rate   | **100%**    |
| Fully Correct Citations | **22 / 25** |
| Minor Issues            | **2 / 25**  |
| Incorrect               | **1 / 25**  |

## JSON Validity Pass Rate

```
Schema:

required:
- answer
- citations
- confidence
```

Validation Rules Applied

Checked for:

- valid JSON structure
- required fields
- correct data types
- enum compliance
- citation array format

JSON Validation Table
| QID | JSON Valid | Issue                                |
| --- | ---------- | ------------------------------------ |
| Q1  | PASS       | —                                    |
| Q2  | PASS       | —                                    |
| Q3  | PASS       | —                                    |
| Q4  | PASS       | —                                    |
| Q5  | PASS       | —                                    |
| Q6  | PASS       | —                                    |
| Q7  | PASS       | —                                    |
| Q8  | FAIL       | Invalid citation key-value structure |
| Q9  | PASS       | —                                    |
| Q10 | PASS       | —                                    |
| Q11 | PASS       | —                                    |
| Q12 | PASS       | —                                    |
| Q13 | PASS       | —                                    |
| Q14 | PASS       | —                                    |
| Q15 | PASS       | —                                    |
| Q16 | PASS       | —                                    |
| Q17 | PASS       | —                                    |
| Q18 | PASS       | —                                    |
| Q19 | PASS       | —                                    |
| Q20 | PASS       | —                                    |
| Q21 | PASS       | —                                    |
| Q22 | PASS       | —                                    |
| Q23 | PASS       | —                                    |
| Q24 | PASS       | —                                    |
| Q25 | PASS       | —                                    |

### JSON Validity Summary

| Metric         | Value       |
| -------------- | ----------- |
| Valid JSON     | **24 / 25** |
| Invalid JSON   | **1 / 25**  |
| JSON Pass Rate | **96%**     |

#### Root Cause of JSON Failure

```
Q8:

"citations": ["section": "7"]

Problem:

Dictionary inside array
instead of string

Correct format:

"citations": ["Section 7"]
```

## Final System-Level Evaluation

| Evaluation Dimension | Score          |
| -------------------- | -------------- |
| Answer Correctness   | **80% strict** |
| Semantic Correctness | **92%**        |
| Citation Accuracy    | **88%**        |
| Citation Presence    | **100%**       |
| JSON Validity        | **96%**        |
| Overall Reliability  | **High**       |
