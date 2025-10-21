from langgraph import Graph, Node
import os, requests
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

# ---------------- Nodes ----------------

def get_pr_files_node(_, context):
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/pulls/{PR_NUMBER}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    files = [f["filename"] for f in resp.json() if f["filename"].endswith(".py")]
    return {"files": files}

def read_file_node(input_data, context):
    file_path = input_data["file"]
    with open(file_path, "r") as f:
        return {"code": f.read()}

def review_code_node(input_data, context):
    code = input_data["code"]
    prompt = f"Review this Python code:\n{code}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=500
    )
    return {"feedback": response.choices[0].message.content}

def post_comment_node(input_data, context):
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {"body": input_data["feedback"]}
    resp = requests.post(url, json=data, headers=headers)
    return {"status": resp.status_code}

# ---------------- Graph ----------------

graph = Graph()
graph.add_node(Node("get_files", get_pr_files_node))
graph.add_node(Node("read_file", read_file_node))
graph.add_node(Node("review_code", review_code_node))
graph.add_node(Node("post_comment", post_comment_node))

# Connect nodes
# For each file, flow: get_files → read_file → review_code → post_comment
# This requires a loop inside graph execution or GPT deciding file per iteration

# ---------------- Run ----------------
graph.run()