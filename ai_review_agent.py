import os
import requests
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Use PAT with repo scope
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Define Tools
# ------------------------------
@tool
def get_pr_files(repo: str, pr_number: int, token: str):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return [f["filename"] for f in resp.json() if f["filename"].endswith(".py")]

@tool
def read_file(file_path: str):
    with open(file_path, "r") as f:
        return f.read()

@tool
def review_code(code: str):
    prompt = f"""
You are an expert Python code reviewer.
Review this code for:
- Bugs or potential issues
- Performance or readability improvements
- Security concerns
- Testing or documentation suggestions

Code:
{code}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return resp.choices[0].message.content

@tool
def post_pr_comment(repo: str, pr_number: int, body: str, token: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {resp.status_code} - {resp.text}"

# ------------------------------
# Create LangGraph Agent
# ------------------------------
agent = create_react_agent(
    model=client,
    tools=[get_pr_files, read_file, review_code, post_pr_comment],
    prompt="You are an autonomous AI code reviewer. Review all Python files in the PR and post comments."
)

# ------------------------------
# Run the Agent
# ------------------------------
if __name__ == "__main__":
    agent.invoke({
        "repo": GITHUB_REPOSITORY,
        "pr_number": PR_NUMBER,
        "token": GITHUB_TOKEN
    })