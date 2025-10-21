import os
import requests
from dotenv import load_dotenv

# LangGraph imports
from langgraph_sdk import ChatOpenAI
from langgraph.prebuilt.chat_agent_executor import create_react_agent, Tool

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT token
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

# ------------------------------
# Define Tools
# ------------------------------

@Tool
def get_pr_files(repo: str, pr_number: int, token: str) -> list[str]:
    """
    Fetch Python files changed in the PR.
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    files = resp.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]


@Tool
def read_file(file_path: str) -> str:
    """
    Read file content from local repo.
    """
    with open(file_path, "r") as f:
        return f.read()


@Tool
def review_code(code: str) -> str:
    """
    Use GPT to review the Python code and provide suggestions.
    """
    prompt = f"""
You are an expert Python code reviewer. Review this code for:
1. Bugs or potential issues
2. Performance/readability improvements
3. Security concerns
4. Testing or documentation suggestions

CODE:
{code}
"""
    # Use a temporary ChatOpenAI client for reviewing
    client = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    response = client.chat(
        messages=[
            {"role": "system", "content": "You are a helpful Python code reviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.content


@Tool
def post_pr_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """
    Post a comment to the GitHub PR.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {resp.status_code} - {resp.text}"


# ------------------------------
# Initialize ChatOpenAI for Agent
# ------------------------------
client = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

# ------------------------------
# Create the Agent
# ------------------------------
agent = create_react_agent(
    model=client,
    tools=[get_pr_files, read_file, review_code, post_pr_comment]
)

# ------------------------------
# Run Agent
# ------------------------------
if __name__ == "__main__":
    system_prompt = """
You are an autonomous AI code reviewer.
1. Fetch all Python files in the current PR.
2. Read their content.
3. Review code for bugs, improvements, security, and tests.
4. Post review comments back to the PR.
Be concise and professional.
"""
    agent.invoke(
        input=f"Review all Python files in PR #{PR_NUMBER} of repo {GITHUB_REPOSITORY}.",
        config={
            "system_prompt": system_prompt,
            "args": {
                "repo": GITHUB_REPOSITORY,
                "pr_number": PR_NUMBER,
                "token": GITHUB_TOKEN
            }
        }
    )