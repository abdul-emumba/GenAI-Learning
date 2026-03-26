# Tokenization Comparison: GPT vs BERT

We compare tokenization between GPT (using tiktoken) and BERT (using transformers) tokenizers to understand how different models handle various text types.

## Token Count Comparison Table

| **String** | **GPT Tokens** | **BERT Tokens** |
|------------|----------------|-----------------|
| Hello world | 2 | 4 |
| عبدالمعید | 9 | 11 |
| Guten Morgen | 4 | 6 |
| Hello سلام Guten Tag | 9 | 10 |
| 👨‍💻 | 7 | 3 |
| 😀😃😄😁 | 8 | 3 |
| https://api.service.com/v1/users?id=123&status=ok | 20 | 24 |
| {"status":"ok","message":"done"} | 9 | 19 |
| SELECT * FROM users WHERE id=123 | 8 | 10 |
| def login(user, password): | 7 | 11 |
| /api/v1/auth/login | 9 | 13 |
| user@example.com | 5 | 7 |
| 192.168.1.1 | 7 | 9 |
| 2025-01-01T10:30:00Z | 13 | 15 |
| ₹1000 | 4 | 5 |
| 中文测试 | 7 | 6 |
| नमस्ते | 12 | 6 |
| مرحبا بالعالم | 12 | 14 |
| {"a":"x"*50} | 8 | 13 |
| [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, ... | 201 | 203 |
| /* Multi-line comment */ int x = 0; | 11 | 15 |
| vector<vector<int>> matrix; | 8 | 11 |
| def reverse_string(s): return s[::-1] | 14 | 18 |
| <html><body>Hello!</body></html> | 12 | 18 |
| function test() { console.log('hi'); } | 11 | 17 |
| 'single quoted' | 4 | 6 |
| "double quoted" | 4 | 6 |
| `backtick string` | 5 | 7 |
| aaaaaaaabbbbbbbbbccccccccccdddddddddd | 17 | 20 |

## Surprises

1. **Complex Emojis – `👨‍💻`**
   - GPT: 7 tokens vs BERT: 3 tokens.
   - **Reason:** GPT's byte-level BPE splits the compound emoji into more sub-tokens, while BERT's WordPiece merges it more efficiently.

2. **Emoji Sequences – `😀😃😄😁`**
   - GPT: 8 tokens vs BERT: 3 tokens.
   - **Reason:** Similar to above, GPT tokenizes each emoji separately at byte level, BERT treats them as fewer units.

3. **JSON Objects – `{"status":"ok","message":"done"}`**
   - GPT: 9 tokens vs BERT: 19 tokens.
   - **Reason:** BERT's WordPiece tokenizes punctuation and short words more granularly, leading to higher token count for structured data.

4. **URLs – `https://api.service.com/v1/users?id=123&status=ok`**
   - GPT: 20 tokens vs BERT: 24 tokens.
   - **Reason:** BERT splits more on punctuation and numbers, increasing token count for complex URLs.

5. **Arabic Text – `عبدالمعید`**
   - GPT: 9 tokens vs BERT: 11 tokens.
   - **Reason:** GPT merges more characters into tokens, while BERT's approach results in finer granularity for non-Latin scripts.

## Key Takeaways

- Tokenization strategies differ significantly between models.
- GPT tends to be more efficient for emojis and some scripts, while BERT is more granular for punctuation-heavy text.
- Understanding these differences is key for optimizing prompts and managing context windows.
