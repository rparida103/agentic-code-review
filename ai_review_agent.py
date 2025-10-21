import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from langgraph.prebuilt.tool import Tool

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GH_PAT")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Tools
# ------------------------------

@Tool
def get_pr_python_files(repo: str, pr_number: int, token: str) -> list[str]:
    """Return a list of Python (.py) files changed in the PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    files = resp.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

@Tool
def read_file(file_path: str) -> str:
    """Return the contents of a local file."""
    with open(file_path, "r") as f:
        return f.read()

@Tool
def review_code(code: str) -> str:
    """Review Python code and provide suggestions, bugs, and best practices."""
    prompt = f"""
You are a senior Python reviewer. Analyze this code and provide:
1. A short summary.
2. Potential bugs or issues.
3. Suggestions for improvement.
4. Testing or documentation recommendations.

CODE:
{code}
"""
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are an expert Python code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content

@Tool
def post_pr_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a comment to a GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {resp.status_code} - {resp.text}"

# ------------------------------
# AI Agent
# ------------------------------

agent = create_react_agent(
    model=client,
    tools=[get_pr_python_files, read_file, review_code, post_pr_comment]
)

# ------------------------------
# Run the agent
# ------------------------------

if __name__ == "__main__":
    repo = GITHUB_REPOSITORY
    pr_number = int(PR_NUMBER)
    token = GITHUB_TOKEN

    prompt = f"""
Review all Python files in PR #{pr_number} in repository {repo}.
For each file:
- Read its content
- Review the code
- Post the review as a comment to the PR
"""
    agent.run(prompt)