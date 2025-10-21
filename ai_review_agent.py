import os
import requests
from openai import OpenAI, function_tool, ai_agent
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

# ======================================================
# 🎯 Define Function Tools
# ======================================================

@function_tool
def get_pr_files(repo: str, pr_number: int, token: str) -> list[str]:
    """
    Fetch a list of Python (.py) files changed in the given GitHub PR.
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]


@function_tool
def read_file(file_path: str) -> str:
    """
    Read and return the contents of a file.
    """
    with open(file_path, "r") as f:
        return f.read()


@function_tool
def review_code(code: str) -> str:
    """
    Review the given Python code for:
    - Bugs or potential issues
    - Performance or readability improvements
    - Security concerns
    - Unit testing or documentation suggestions
    """
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
        max_tokens=700,
        messages=[
            {"role": "system", "content": "You are an expert software reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


@function_tool
def post_pr_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """
    Post a comment to the specified GitHub PR.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {response.status_code} - {response.text}"


# ======================================================
# 🧠 Define the AI Agent
# ======================================================

@ai_agent(
    name="AI Code Reviewer",
    model="gpt-4o-mini",
    instructions="""
You are an autonomous code review assistant that:
1. Fetches all changed Python files in the current PR.
2. Reads their content.
3. Reviews the code using the review_code tool.
4. Posts review comments back to the PR.
Be concise and professional in your feedback.
""",
    tools=[get_pr_files, read_file, review_code, post_pr_comment],
)
def ai_reviewer(agent):
    """
    Main AI agent that coordinates code review using the defined tools.
    """
    repo = GITHUB_REPOSITORY
    pr_number = int(PR_NUMBER)
    token = GITHUB_TOKEN

    agent.log("Fetching Python files in PR...")
    files = get_pr_files(repo, pr_number, token)
    if not files:
        agent.log("No Python files found in this PR.")
        return

    for file_path in files:
        agent.log(f"Reviewing: {file_path}")
        code = read_file(file_path)
        feedback = review_code(code)
        post_pr_comment(repo, pr_number, f"### 🤖 AI Review for `{file_path}`\n{feedback}", token)
        agent.log(f"Review posted for {file_path} ✅")


# ======================================================
# 🚀 Main
# ======================================================

if __name__ == "__main__":
    print("=== 🤖 Starting Autonomous AI Code Reviewer ===")
    ai_reviewer.run("Review all changed Python files in the current PR and comment feedback.")