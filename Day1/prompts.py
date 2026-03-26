from groq import Groq

client = Groq()
print("Groq client initialized successfully.")

prompts = [
    "Explain LLM in one sentence.",
    "Write a Python function to reverse a string.",
    "Give 3 reasons microservices fail in production.",
    "Summarize Kubernetes autoscaling in 20 words.",
    "Write a creative product name for an AI log analyzer.",
    "Explain memory leaks in Go services.",
    "Return valid JSON with fields: status, message.",
    "Translate to Urdu: Environment is down.",
    "List 5 edge cases for API authentication.",
    "Write a short story about a software engineer."
]

temps = [0, 0.7, 1]

for prompt in prompts:
    print("\n" + "=" * 60)
    print("PROMPT:", prompt)

    for t in temps:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",

            temperature=t,
            max_tokens=300,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print(f"\nTemperature {t}:")
        print(response.choices[0].message.content)