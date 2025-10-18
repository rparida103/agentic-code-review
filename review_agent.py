import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

client = OpenAI(api_key=OPENAI_API_KEY)


def get_pr_files(repo, pr_number, token):
    """Fetch list of files changed in a PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    # Filter only Python files
    return [f["filename"] for f in files if f["filename"].endswith(".py")]


def review_code(file_path):
    """Review code using OpenAI."""
    with open(file_path, "r") as f:
        code = f.read()

    prompt = f"""
You are a senior software engineer. Review the following Python code
for bugs, improvements, best practices, and testing suggestions.
Provide detailed explanation and suggestions.

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
    return response.choices[0].message.content


def main():
    print("=== AI Code Review for Python Files in PR ===")
    python_files = get_pr_files(GITHUB_REPOSITORY, PR_NUMBER, GITHUB_TOKEN)

    if not python_files:
        print("No Python files changed in this PR.")
        return

    for file_path in python_files:
        print(f"\n--- Reviewing: {file_path} ---")
        feedback = review_code(file_path)
        print(feedback)


if __name__ == "__main__":
    main()