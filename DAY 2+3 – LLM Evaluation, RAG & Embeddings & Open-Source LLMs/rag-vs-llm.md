# RAG vs Full-Text LLM Answering — Comparison

---

# Objective

Compare a **basic RAG pipeline** with **full-text LLM answering** to evaluate:

* Answer correctness
* Failure cases
* Practical usefulness of basic RAG

---

# Results Comparison

## RAG vs Full-Text LLM Answering

**Full-Text LLM**

* Higher recall
* Answers using internal knowledge
* Works even when retrieval is not needed

**Basic RAG**

* Produces grounded answers
* Depends heavily on retrieval quality
* Avoids guessing when context is missing

**Key Insight**

Full-text LLM performs better on simple factual questions, while RAG is safer but more sensitive to retrieval errors.

---

# Answer Correctness

**Observed Accuracy (approx.)**

* Full-text LLM: Higher correctness overall
* Basic RAG: Lower correctness due to retrieval limitations

**Important Pattern**

Most incorrect answers in RAG were not reasoning errors.

They were retrieval failures.

---

# Failure Cases

## 1) Missed Information (Most Common)

* Relevant content exists
* Retriever did not return the correct chunk

Root Cause:

Retrieval recall limitation

---

## 2) Hallucination (Rare)

* Model added extra details not in context

Observation:

Grounding significantly reduced hallucination risk

---

## 3) Truncation / Context Limitation

* Important information split across chunks
* Model received incomplete context

---

# Conclusion

## Where Basic RAG Helped

* Reduced hallucinations
* Correctly handled "not-in-document" questions
* Produced reliable answers when correct context was retrieved

## Where Basic RAG Did Not Help

* Simple factual questions requiring precise retrieval
* Cases where retriever missed relevant chunks
* Overall performance limited by retrieval quality

**Final Insight**

Basic RAG improves answer reliability but reduces recall. System performance is primarily determined by retrieval quality, not model reasoning ability.
