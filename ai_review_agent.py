import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GH_PAT")  # Personal Access Token
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Define Python "tools"
# ------------------------------

def list_python_files(repo: str, pr_number: int, token: str) -> list[str]:
    """Return list of Python files changed in a PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

def read_file(file_path: str) -> str:
    """Read the local file content."""
    with open(file_path, "r") as f:
        return f.read()

def code_review(code: str) -> str:
    """Generate AI review feedback for Python code."""
    prompt = f"""
You are a senior Python reviewer. Review this code for:
1. Bugs or issues
2. Performance or readability improvements
3. Security concerns
4. Testing or documentation suggestions

CODE:
{code}
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an expert Python reviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content

def post_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a comment to the GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return f"✅ Comment posted for PR {pr_number}"
    else:
        return f"❌ Failed to post comment: {response.status_code} - {response.text}"

# ------------------------------
# Define OpenAI SDK tools
# ------------------------------
tools = [
    {
        "name": "list_python_files",
        "description": "Get all Python files changed in a PR.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "pr_number": {"type": "integer"},
                "token": {"type": "string"}
            },
            "required": ["repo", "pr_number", "token"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a local file and return its contents.",
        "parameters": {
            "type": "object",
            "properties": {"file_path": {"type": "string"}},
            "required": ["file_path"]
        }
    },
    {
        "name": "code_review",
        "description": "Analyze Python code and return review comments.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"]
        }
    },
    {
        "name": "post_comment",
        "description": "Post a comment to the PR on GitHub.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "pr_number": {"type": "integer"},
                "body": {"type": "string"},
                "token": {"type": "string"}
            },
            "required": ["repo", "pr_number", "body", "token"]
        }
    }
]

# ------------------------------
# Map tool names to actual Python functions
# ------------------------------
func_map = {
    "list_python_files": list_python_files,
    "read_file": read_file,
    "code_review": code_review,
    "post_comment": post_comment
}

# ------------------------------
# Autonomous AI prompt
# ------------------------------
prompt = f"""
You are an autonomous AI code reviewer.
1. Fetch all Python files in PR {PR_NUMBER} of repo {GITHUB_REPO}.
2. Read each file.
3. Review the code for bugs, improvements, security, and testing.
4. Post review comments back to the PR.
"""

# ------------------------------
# Call the AI with tools
# ------------------------------
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    functions=tools,
    function_call="auto"
)

message = response.choices[0].message

if message.function_call:
    func_name = message.function_call.name
    args = json.loads(message.function_call.arguments)

    # Inject token automatically if needed
    if func_name in ["list_python_files", "post_comment"]:
        args["token"] = GITHUB_TOKEN

    print(f"AI called tool: {func_name} with args: {args}")

    # Execute the selected tool
    if func_name in func_map:
        result = func_map[func_name](**args)
        print("Result:", result)