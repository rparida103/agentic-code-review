from langgraph.prebuilt.chat_agent_executor import create_react_agent
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- Tools as functions ----------------

def get_pr_files(repo: str, pr_number: int, token: str):
    """Fetch all Python files changed in a GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return [f["filename"] for f in resp.json() if f["filename"].endswith(".py")]

def read_file(file_path: str):
    """Read a Python file and return its content."""
    with open(file_path, "r") as f:
        return f.read()

def review_code(code: str):
    """Review Python code for bugs, improvements, security, and tests."""
    prompt = f"""
You are a senior Python code reviewer.
Analyze this code for:
1. Bugs or potential issues
2. Performance/readability improvements
3. Security concerns
4. Testing or documentation recommendations

Code:
{code}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are a helpful AI code reviewer."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content

def post_pr_comment(repo: str, pr_number: int, body: str, token: str):
    """Post a comment on a GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {resp.status_code} - {resp.text}"

# ---------------- Create agent ----------------

agent = create_react_agent(
    model=client,
    tools=[get_pr_files, read_file, review_code, post_pr_comment],
    instructions="""
You are an autonomous AI code reviewer.
1. Fetch all Python files in the current PR.
2. Read their content.
3. Review the code for bugs, improvements, security, and tests.
4. Post review comments back to the PR.
Provide concise and actionable feedback.
"""
)

# ---------------- Run agent ----------------

if __name__ == "__main__":
    agent.run(
        repo=GITHUB_REPOSITORY,
        pr_number=PR_NUMBER,
        token=GITHUB_TOKEN
    )