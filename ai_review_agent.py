import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from tools.list_files_tool import list_python_files, tool_spec as list_files_tool_spec
from tools.read_file_tool import read_file, tool_spec as read_file_tool_spec
from tools.code_review_tool import code_review, tool_spec as code_review_tool_spec
from tools.post_comment_tool import post_comment, tool_spec as post_comment_tool_spec

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER", "0"))

MODEL = "gpt-4o-mini"

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Combine all tool specs
# ------------------------------
tools = [
    list_files_tool_spec,
    read_file_tool_spec,
    code_review_tool_spec,
    post_comment_tool_spec,
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
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    tools=tools,
    tool_choice="auto",
)

message = response.choices[0].message

# ------------------------------
# Step 2: Execute the AI’s chosen tool
# ------------------------------
tool_calls = getattr(message, "tool_calls", [])
for tool_call in tool_calls:
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    # Secure token injection
    if func_name in ["list_python_files", "post_comment"]:
        args["token"] = GITHUB_TOKEN

    print(f"AI called tool: {func_name} with args: {args}")

    func_map = {
        "list_python_files": list_python_files,
        "read_file": read_file,
        "code_review": code_review,
        "post_comment": post_comment,
    }

    if func_name in func_map:
        result = func_map[func_name](**args)
        print(f"Tool result: {result}")

        # ------------------------------
        # Step 3: Review each Python file
        # ------------------------------
        python_files = result if isinstance(result, list) else []
        for file_path in python_files:
            print(f"\n Reviewing file: {file_path}")
            try:
                code = read_file(file_path)
                feedback = code_review(code)
                print(f"\n Review for {file_path}:\n{feedback}\n")
                comment_status = post_comment(
                    GITHUB_REPO,
                    PR_NUMBER,
                    f"**{file_path}**\n\n{feedback}",
                    GITHUB_TOKEN,
                )
                print(comment_status)
            except Exception as e:
                print(f" Error reviewing {file_path}: {e}")
if not tool_calls:
    print("No tool call detected from AI.")
