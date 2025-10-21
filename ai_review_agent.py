from langgraph import Builder, Tool
import os, requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_pr_files(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return [f["filename"] for f in resp.json() if f["filename"].endswith(".py")]

def read_file(file_path):
    with open(file_path) as f:
        return f.read()

def review_code(code):
    prompt = f"Review this code:\n{code}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return resp.choices[0].message.content

def post_pr_comment(repo, pr_number, body, token):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    resp = requests.post(url, json={"body": body}, headers=headers)
    return resp.status_code

# Wrap as LangGraph tools
tools = [
    Tool(name="get_pr_files", func=get_pr_files),
    Tool(name="read_file", func=read_file),
    Tool(name="review_code", func=review_code),
    Tool(name="post_pr_comment", func=post_pr_comment)
]

# Build and run
builder = Builder(tools=tools)
builder.run(input_data={
    "repo": os.getenv("GITHUB_REPOSITORY"),
    "pr_number": int(os.getenv("PR_NUMBER")),
    "token": os.getenv("GITHUB_TOKEN")
})