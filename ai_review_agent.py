import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.prebuilt.chat_agent_executor import create_react_agent

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ======================================================
# 🎯 Define Tools
# ======================================================

def get_pr_files(repo: str, pr_number: int, token: str):
    """Fetch all Python (.py) files changed in the given GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return [f["filename"] for f in resp.json() if f["filename"].endswith(".py")]


def read_file(file_path: str):
    """Read and return the contents of a file."""
    with open(file_path, "r") as f:
        return f.read()


def review_code(code: str):
    """Review the given Python code for bugs, improvements, and best practices."""
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
        model="gpt-4o-mini",
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are a helpful AI code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def post_pr_comment(repo: str, pr_number: int, body: str, token: str):
    """Post a comment to the specified GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {resp.status_code} - {resp.text}"

# ======================================================
# 🧠 Create AI Agent
# ======================================================

agent = create_react_agent(
    model=client,
    tools=[get_pr_files, read_file, review_code, post_pr_comment]
)

# ======================================================
# 🚀 Run Agent
# ======================================================

if __name__ == "__main__":
    print("=== 🤖 Starting AI Code Reviewer ===")
    repo = GITHUB_REPOSITORY
    pr_number = PR_NUMBER
    token = GITHUB_TOKEN

    # Add your high-level instruction here as the first message
    system_prompt = """
You are an autonomous AI code reviewer.
1. Fetch all Python files in the current PR.
2. Read their content.
3. Review the code for bugs, improvements, and security.
4. Post review comments back to the PR.
Provide concise and actionable feedback.
"""

    result = agent.invoke(
        input=f"Review all changed Python files in repo {repo}, PR #{pr_number}.",
        config={
            "system_prompt": system_prompt,
            "args": {"repo": repo, "pr_number": pr_number, "token": token}
        },
    )

    print("=== ✅ Review Completed ===")
    print(result)