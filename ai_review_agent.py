import os
import requests
from dotenv import load_dotenv
from langgraph import Builder, Tool, ChatAgentExecutor
from openai import OpenAI

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Your PAT token
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Define Tools
# ------------------------------

def get_pr_files(repo: str, pr_number: int, token: str):
    """Fetch all Python files changed in a GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return [f["filename"] for f in resp.json() if f["filename"].endswith(".py")]

def read_file(file_path: str):
    """Read a local Python file and return its content."""
    with open(file_path, "r") as f:
        return f.read()

def review_code(code: str):
    """Review Python code and return feedback."""
    prompt = f"""
You are an expert Python code reviewer.
Analyze this code for:
- Bugs or potential issues
- Performance/readability improvements
- Security concerns
- Testing or documentation recommendations

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

# Wrap tools for LangGraph
tg_get_pr_files = Tool(name="get_pr_files", description="Get Python files changed in PR", func=get_pr_files)
tg_read_file = Tool(name="read_file", description="Read a Python file", func=read_file)
tg_review_code = Tool(name="review_code", description="Review Python code", func=review_code)
tg_post_pr_comment = Tool(name="post_pr_comment", description="Post comment to PR", func=post_pr_comment)

# ------------------------------
# Build the Agent
# ------------------------------
builder = Builder(name="AI PR Reviewer", model=client)
builder.add_tools([tg_get_pr_files, tg_read_file, tg_review_code, tg_post_pr_comment])
builder.set_instructions(
    """
You are an autonomous AI code reviewer.
1. Fetch all Python files in the PR.
2. Read the file content.
3. Review the code.
4. Post review comments back to GitHub.
Provide concise and actionable feedback.
"""
)

agent = builder.build()

# ------------------------------
# Run Agent
# ------------------------------
if __name__ == "__main__":
    print("=== 🤖 Starting AI PR Reviewer ===")
    agent.run(
        repo=GITHUB_REPOSITORY,
        pr_number=PR_NUMBER,
        token=GITHUB_TOKEN
    )