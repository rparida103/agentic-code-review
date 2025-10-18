import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Fetch changed Python files in PR
# ------------------------------
def get_pr_files(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

# ------------------------------
# Review code using OpenAI
# ------------------------------
def review_code(file_path):
    with open(file_path, "r") as f:
        code = f.read()

    prompt = f"""
You are a senior software engineer. Review the following Python code
for bugs, improvements, best practices, and testing suggestions.
Provide clear, actionable feedback.

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

# ------------------------------
# Post comment to GitHub PR
# ------------------------------
def post_pr_comment(repo, pr_number, file_path, body, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {
        "body": body,
        "path": file_path,
        "position": 1  # Always comment at the top; adjust if needed
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"✅ Comment added to {file_path}")
    else:
        print(f"❌ Failed to comment on {file_path}: {response.status_code} - {response.text}")

# ------------------------------
# Main execution
# ------------------------------
def main():
    print("=== AI Code Review and PR Comments ===")
    python_files = get_pr_files(GITHUB_REPOSITORY, PR_NUMBER, GITHUB_TOKEN)

    if not python_files:
        print("No Python files changed in this PR.")
        return

    for file_path in python_files:
        print(f"\n--- Reviewing: {file_path} ---")
        feedback = review_code(file_path)
        print(feedback)
        post_pr_comment(GITHUB_REPOSITORY, PR_NUMBER, file_path, feedback, GITHUB_TOKEN)

if __name__ == "__main__":
    main()