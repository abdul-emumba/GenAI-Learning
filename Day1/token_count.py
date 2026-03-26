from transformers import AutoTokenizer

tok_gpt = AutoTokenizer.from_pretrained("gpt2")
tok_bert = AutoTokenizer.from_pretrained("bert-base-uncased")

strings = [
    "Hello world",
    "عبدالمعید",   
    "Guten Morgen",
    "Hello سلام Guten Tag",
    "👨‍💻",
    "😀😃😄😁",
    "https://api.service.com/v1/users?id=123&status=ok",
    '{"status":"ok","message":"done"}',
    "SELECT * FROM users WHERE id=123",
    "def login(user, password):",
    "/api/v1/auth/login",
    "user@example.com",
    "192.168.1.1",
    "2025-01-01T10:30:00Z",
    "₹1000",
    "中文测试",
    "नमस्ते",
    "مرحبا بالعالم",
    '{"a":"x"*50}',
    "[" + ", ".join(str(i) for i in range(100)) + "]",
    "/* Multi-line comment */ int x = 0;",
    "vector<vector<int>> matrix;",
    "def reverse_string(s): return s[::-1]",
    "<html><body>Hello!</body></html>",
    "function test() { console.log('hi'); }",
    "'single quoted'",
    '"double quoted"',
    "`backtick string`",
    "aaaaaaaabbbbbbbbbccccccccccdddddddddd"
]

print(f"{'STRING':<60} | {'GPT Tokens':<10} | {'BERT Tokens':<10}")
print("-" * 86)

for s in strings:
    gpt_len = len(tok_gpt.encode(s))
    bert_len = len(tok_bert.encode(s))
    snippet = (s[:55] + "...") if len(s) > 55 else s
    print(f"{snippet:<60} | {gpt_len:<10} | {bert_len:<10}")