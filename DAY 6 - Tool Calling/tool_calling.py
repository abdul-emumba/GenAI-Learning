from groq import Groq
import json

client = Groq()
MODEL = "openai/gpt-oss-120b"

def calculate(expression: str):
    try:
        result = eval(expression, {"__builtins__": {}})
        return json.dumps({"result": result})
    except Exception:
        return json.dumps({"error": "Invalid expression"})


DOCUMENTS = [
    {"id": 1, "city": "lahore", "category": "food", "text": "Best biryani spots in Lahore"},
    {"id": 2, "city": "karachi", "category": "tech", "text": "Top startups in Karachi"},
    {"id": 3, "city": "islamabad", "category": "food", "text": "Fine dining in Islamabad"},
    {"id": 4, "city": "lahore", "category": "tech", "text": "Software houses in Lahore"},
]

def retrieve_documents(city: str = None, category: str = None):
    results = DOCUMENTS

    if city:
        results = [d for d in results if d["city"] == city.lower()]
    if category:
        results = [d for d in results if d["category"] == category.lower()]

    return json.dumps({"results": results})


def validate_tool_call(tool_name, args):
    if tool_name == "calculate":
        if "expression" not in args:
            raise ValueError("Missing 'expression'")
        if not isinstance(args["expression"], str):
            raise ValueError("expression must be string")

    elif tool_name == "retrieve_documents":
        allowed = {"city", "category"}

        for key in args:
            if key not in allowed:
                raise ValueError(f"Invalid field: {key}")

        if not any(k in args for k in allowed):
            raise ValueError("At least one of city/category required")

    else:
        raise ValueError("Unknown tool")


def run_conversation(user_prompt):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a smart assistant.\n"
                "- Use tools ONLY when needed.\n"
                "- For math → use calculate\n"
                "- For retrieval → use retrieve_documents\n"
                "- retrieve_documents ONLY accepts:\n"
                "   city (string), category (string)\n"
                "- DO NOT invent parameters like 'query'\n"
            )
        },
        {"role": "user", "content": user_prompt},
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Evaluate math expression",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    },
                    "required": ["expression"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_documents",
                "description": "Filter documents by city/category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "category": {"type": "string"},
                    },
                },
            },
        },
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    msg = response.choices[0].message
    tool_calls = msg.tool_calls

    if tool_calls:
        messages.append(msg)

        available_functions = {
            "calculate": calculate,
            "retrieve_documents": retrieve_documents,
        }

        for call in tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)

            try:
                validate_tool_call(name, args)

                result = available_functions[name](**args)

            except Exception as e:
                messages.append({
                    "role": "system",
                    "content": f"Tool call failed due to: {str(e)}. Fix arguments and retry."
                })
                
                retry_response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )

                return retry_response.choices[0].message.content

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": result,
            })

        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="none",
        )

        return second_response.choices[0].message.content

    return msg.content