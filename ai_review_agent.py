import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT token
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Tool Functions
# ------------------------------

def list_python_files(repo: str, pr_number: int, token: str) -> list[str]:
    """Return list of Python files changed in the PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    files = resp.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

def read_file(file_path: str) -> str:
    """Return the content of a local file."""
    with open(file_path, "r") as f:
        return f.read()

def code_review(code: str) -> str:
    """Review Python code for bugs, improvements, security, and testing suggestions."""
    prompt = f"""
You are a senior Python reviewer. Analyze this code carefully and provide:
1. A short summary of what the code does.
2. Potential bugs or issues.
3. Suggestions for improvement.
4. Testing or documentation recommendations.

CODE:
{code}
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are an expert software reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def post_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a comment to the GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to post comment: {resp.status_code} - {resp.text}"

# ------------------------------
# Main AI Reviewer
# ------------------------------

def ai_pr_reviewer():
    repo = GITHUB_REPOSITORY
    pr_number = int(PR_NUMBER)
    token = GITHUB_TOKEN

    print("Fetching Python files in PR...")
    files = list_python_files(repo, pr_number, token)
    if not files:
        print("No Python files found in this PR.")
        return

    for file_path in files:
        print(f"Reviewing: {file_path}")
        code = read_file(file_path)
        feedback = code_review(code)
        result = post_comment(repo, pr_number, f"### 🤖 AI Review for `{file_path}`\n{feedback}", token)
        print(result)

# ------------------------------
# Run
# ------------------------------

if __name__ == "__main__":
    print("=== 🤖 Starting AI PR Reviewer ===")
    ai_pr_reviewer()