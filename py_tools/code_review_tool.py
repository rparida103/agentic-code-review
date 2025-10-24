from openai import OpenAI

MODEL = "gpt-4o-mini"
client = OpenAI()

def code_review(code: str) -> str:
    """Analyze Python code and return review feedback."""
    prompt = f"""
        You are a senior Python reviewer. Review this code for:
            1. Bugs or issues
            2. Improvements for readability and performance
            3. Security concerns
            4. Testing or documentation suggestions

        CODE:
        {code}
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert Python reviewer."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=600,
    )
    return response.choices[0].message.content

tool_spec = {
    "type": "function",
    "function": {
        "name": "code_review",
        "description": "Analyze Python code and return review feedback.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
            },
            "required": ["code"],
        },
    },
}