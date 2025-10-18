from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def review_code(file_path):
    with open(file_path, "r") as f:
        code = f.read()

    prompt = f"""
    You are a senior software engineer. Review the following Python code
    for bugs, improvements, best practices, and testing suggestions.

    CODE:
    {code}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful AI code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    print("=== AI Code Review Feedback ===")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    review_code("app.py")