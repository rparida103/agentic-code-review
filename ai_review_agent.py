import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------
# Setup
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER", "0"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Tool Implementations
# ------------------------------
def list_python_files(repo: str, pr_number: int, token: str) -> list[str]:
    """Return list of Python files changed in the PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

def read_file(file_path: str) -> str:
    """Return the content of a local file."""
    with open(file_path, "r") as f:
        return f.read()

def code_review(code: str) -> str:
    """Analyze Python code and return review feedback."""
    prompt = f"""
You are a senior Python reviewer. Review this code for:
1. Bugs or issues
2. Improvements for readability and performance
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
    return response.choices[0].message.content.strip()

def post_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a comment to the GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return "✅ Comment posted successfully"
    else:
        return f"❌ Failed to comment: {response.status_code} - {response.text}"

# ------------------------------
# Tool definitions for OpenAI SDK
# ------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_python_files",
            "description": "Get all Python files changed in the PR.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"},
                    "token": {"type": "string"}
                },
                "required": ["repo", "pr_number", "token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a local file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "code_review",
            "description": "Analyze Python code and return review comments.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
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
    }
]

# ------------------------------
# AI Agent logic
# ------------------------------
prompt = f"""
You are an autonomous AI code reviewer.
1. Fetch all Python files in PR {PR_NUMBER} of repo {GITHUB_REPO}.
2. Read each file.
3. Review the code for bugs, improvements, and best practices.
4. Post review comments back to the PR.
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message

# ------------------------------
# Handle tool calls dynamically
# ------------------------------
func_map = {
    "list_python_files": list_python_files,
    "read_file": read_file,
    "code_review": code_review,
    "post_comment": post_comment
}

if message.tool_calls:
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")

        # 🔐 Force token injection
        if func_name in ["list_python_files", "post_comment"]:
            if not GITHUB_TOKEN:
                raise ValueError("❌ Missing GitHub token (GH_PAT or GITHUB_TOKEN)")
            args["token"] = GITHUB_TOKEN

        print(f"\n🧠 AI called tool: {func_name} with args: {args}")

        if func_name in func_map:
            result = func_map[func_name](**args)
            print("✅ Tool result:", result)
        else:
            print(f"⚠️ Unknown tool called: {func_name}")
else:
    print("⚠️ No tool calls made by AI")