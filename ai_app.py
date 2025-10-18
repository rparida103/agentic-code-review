from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(prompt: str) -> str:
    """
    Send a prompt to OpenAI and return the response.
    """
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def main():
    print("=== Mini AI Assistant App ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        ai_response = ask_ai(user_input)
        print(f"AI: {ai_response}\n")


if __name__ == "__main__":
    main()