# RAGAgent Multi-Turn ReAct + Memory Analysis

## Test Turns

```python
test_turns = [
    "What food places do you have in Lahore?",
    "What about tech stuff in the same city?",
    "If I visit 3 places a day, how many days to visit all 6 documents",
    "And how many in Islamabad?",
    "Compare that to Karachi — what options exist there?",
    "List all the food document titles you retrieved earlier in our conversation."
]
```

---

## Agent Output

```
[Turn 1/6]
USER: What food places do you have in Lahore?
  [ReAct step 1] ACT → retrieve_documents({'category': 'food', 'city': 'lahore'})
  [ReAct step 1] OBSERVE → ok
  [ReAct step 2] STOP → final answer produced
ASSISTANT: Best Biryani Spots in Lahore.

[Turn 2/6]
USER: What about tech stuff in the same city?
  [ReAct step 1] ACT → retrieve_documents({'category': 'tech', 'city': 'lahore'})
  [ReAct step 1] OBSERVE → ok
  [ReAct step 2] STOP → final answer produced
ASSISTANT: Software houses in Lahore.

[Turn 3/6]
USER: If I visit 3 places a day, how many days to visit all 6 documents?
  [ReAct step 1] STOP → final answer produced
ASSISTANT: 2 days (6 / 3 = 2).

[Turn 4/6]
USER: And how many in Islamabad?
  [ReAct step 1] ACT → retrieve_documents({'city': 'islamabad'})
  [ReAct step 1] OBSERVE → ok
  [ReAct step 2] STOP → final answer produced
ASSISTANT: 2 documents in Islamabad (food + tech).

[Turn 5/6]
USER: Compare that to Karachi — what options exist there?
  [ReAct step 1] ACT → retrieve_documents({'city': 'karachi'})
  [ReAct step 1] OBSERVE → ok
  [ReAct step 2] STOP → final answer produced
ASSISTANT: Karachi has 2 documents: Top startups in Karachi (tech),
Street food gems in Karachi (food).
Compared to Lahore which had only a tech listing, Karachi offers both.

[Turn 6/6]
USER: List all the food document titles you retrieved earlier in our conversation.
  [ReAct step 1] ACT → retrieve_documents({'category': 'food', 'city': 'islamabad'})
  [ReAct step 1] OBSERVE → ok
  [ReAct step 2] ACT → retrieve_documents({'category': 'food', 'city': 'karachi'})
  [ReAct step 2] OBSERVE → ok
  [ReAct step 3] STOP → final answer produced
ASSISTANT: Fine dining in Islamabad, Street food gems in Karachi.
```

---

## Correct Agent Decisions

| Turn | Query | Decision | Why correct |
|------|-------|----------|-------------|
| 1 | Food places in Lahore | Retrieve with city + category | Both params explicit in query |
| 2 | Tech in same city | Retrieve, resolved city from memory | "Same city" correctly mapped to lahore via prior turn |
| 3 | Days to visit 6 places | Answer inline, no tool | Number 6 given explicitly, arithmetic trivial |
| 4 | How many in Islamabad | Retrieve without category filter | Broad query, one call returns both categories |
---

## Memory Fault Cases

### Fault 1 - Lahore food doc dropped from comparison (Turn 5)

**What agent said:** "Lahore had only a tech listing."

**What was true:** Turn 1 retrieved `Best Biryani Spots in Lahore` (food). Turn 2 retrieved `Software houses in Lahore` (tech). Lahore had both.

### Fault 2 - Re-retrieved instead of recalling (Turn 6)

**What agent did:** Fired 2 live `retrieve_documents` calls for Islamabad and Karachi food.

**What agent should have done:** Read memory. All food titles were already in conversation history:

- Turn 1: `Best Biryani Spots in Lahore`
- Turn 4: `Fine dining in Islamabad`
- Turn 5: `Street food gems in Karachi`

**Result was also incomplete:** Lahore food doc was never re-fetched in turn 6 so it was missing from the final answer entirely.

---
