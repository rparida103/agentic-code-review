import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT token
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

# -----------------------
# Define tools
# -----------------------
def list_python_files(pr_number: int) -> list[str]:
    """Fetch Python files changed in a PR."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    files = resp.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

def read_file(file_path: str) -> str:
    """Read a local Python file."""
    with open(file_path, "r") as f:
        return f.read()

def review_code(code: str) -> str:
    """Ask AI to review the code and return feedback."""
    prompt = f"""
You are an expert Python reviewer. Analyze this code:

{code}

Provide:
1. Summary
2. Bugs or issues
3. Suggestions
4. Testing recommendations

Output as plain text.
"""
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return resp.choices[0].message.content

def post_comment(comment: str) -> bool:
    """Post a comment to the PR."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {"body": comment}
    resp = requests.post(url, headers=headers, json=data)
    return resp.status_code == 201

# -----------------------
# Agent orchestrator
# -----------------------
TOOLS = {
    "list_python_files": list_python_files,
    "read_file": read_file,
    "review_code": review_code,
    "post_comment": post_comment
}

def run_agent():
    conversation = [
        {"role": "system", "content": "You are an AI code review assistant. Respond only in JSON format with 'tool' and 'args' fields."},
        {"role": "user", "content": "Review all Python files in the PR and post feedback as comments."}
    ]

    # Keep track of tool outputs
    memory = {}

    while True:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=conversation,
            max_tokens=500
        )
        output_text = resp.choices[0].message.content.strip()
        print("AI:", output_text)

        # Parse AI response as JSON
        try:
            action = json.loads(output_text)
            tool_name = action["tool"]
            args = action.get("args", {})
        except json.JSONDecodeError:
            print("⚠️ AI response is not valid JSON. Ending loop.")
            break

        # Execute the tool
        if tool_name in TOOLS:
            result = TOOLS[tool_name](**args)
            conversation.append({"role": "assistant", "content": output_text})
            conversation.append({"role": "system", "content": json.dumps({"tool_result": result})})
        else:
            print(f"⚠️ Unknown tool: {tool_name}")
            break

        # Termination condition
        if action.get("done"):
            print("✅ Agent completed review.")
            break

        time.sleep(1)  # small delay to avoid rate limits

if __name__ == "__main__":
    run_agent()