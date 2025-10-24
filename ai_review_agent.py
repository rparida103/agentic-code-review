import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER", "0"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Tool functions
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
        max_tokens=600,
    )
    return response.choices[0].message.content

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
# Define tools in OpenAI SDK format
# ------------------------------
tools = [
    {
        "name": "list_python_files",
        "description": "Get all Python files changed in the PR.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "pr_number": {"type": "integer"},
                "token": {"type": "string"},
            },
            "required": ["repo", "pr_number", "token"],
        },
    },
]

# ------------------------------
# Step 1: Ask the AI to decide what to do
# ------------------------------
prompt = f"""
You are an autonomous AI code reviewer.
Your goal is to:
1. Fetch all Python files in PR #{PR_NUMBER} from repo {GITHUB_REPO}.
2. Review each file for bugs, improvements, security, and tests.
3. Post feedback as GitHub PR comments.

Start by listing the Python files using the available tool.
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    tools=tools,
    tool_choice="auto",
)

message = response.choices[0].message

# ------------------------------
# Step 2: Execute the AI’s chosen tool
# ------------------------------
if message.tool_calls:
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Secure token injection
        if func_name in ["list_python_files", "post_comment"]:
            args["token"] = GITHUB_TOKEN

        print(f"🧠 AI called tool: {func_name} with args: {args}")

        func_map = {
            "list_python_files": list_python_files,
            "read_file": read_file,
            "code_review": code_review,
            "post_comment": post_comment,
        }

        if func_name in func_map:
            result = func_map[func_name](**args)
            print(f"✅ Tool result: {result}")

            # ------------------------------
            # Step 3: Review each Python file
            # ------------------------------
            python_files = result if isinstance(result, list) else []
            for file_path in python_files:
                print(f"\n📄 Reviewing file: {file_path}")
                try:
                    code = read_file(file_path)
                    feedback = code_review(code)
                    print(f"\n💬 Review for {file_path}:\n{feedback}\n")
                    comment_status = post_comment(
                        GITHUB_REPO,
                        PR_NUMBER,
                        f"**{file_path}**\n\n{feedback}",
                        GITHUB_TOKEN,
                    )
                    print(comment_status)
                except Exception as e:
                    print(f"⚠️ Error reviewing {file_path}: {e}")

else:
    print("⚠️ No tool call detected from AI.")