# Strategy Report: Long-Input Summarization

## Wins by Question Type

- **Naive Stuffing**: Wins for basic summaries, JSON outputs, tables, structured formats (Prompts 1,2,7,9). Full context ensures coherence and valid schemas.
- **Summarize-Then-Answer**: Wins for conditional tasks, factual extraction, trend inference, nested lists (Prompts 3,5,6,8). Chunking preserves details and enables cross-chunk synthesis.

**Overall**: 50/50 split; choice depends on task type.

## Improvement Suggestions

1. **Hybrid Approach**: Use Naive for <2k words; Chunking for longer texts.
2. **Better Chunking**: Semantic splits (by topics) with 20-30% overlap.
3. **Enhanced Summarization**: Add intermediate prompts for key facts; validate coverage.
4. **Intelligent Synthesis**: Fuse chunk summaries with original excerpts for balance.
5. **Quality Metrics**: Track coverage, accuracy, refusal rates; tune temperature (0.3 for summaries, 0.7 for inference).
6. **Parameter Tuning**: Lower temperature for deterministic outputs; adjust max_tokens per task.
