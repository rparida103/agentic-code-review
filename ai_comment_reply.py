import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
BOT_USERNAME = os.getenv("BOT_USERNAME", "rparida103")
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")
GITHUB_EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")
PR_NUMBER = os.getenv("PR_NUMBER")

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Load GitHub event payload
# ------------------------------
with open(GITHUB_EVENT_PATH, "r") as f:
    event = json.load(f)

if GITHUB_EVENT_NAME == "issue_comment":
    comment_id = event["comment"]["id"]
    comment_body = event["comment"]["body"]
    comment_user = event["comment"]["user"]["login"]
    comment_type = "general"
elif GITHUB_EVENT_NAME == "pull_request_review_comment":
    comment_id = event["comment"]["id"]
    comment_body = event["comment"]["body"]
    comment_user = event["comment"]["user"]["login"]
    comment_type = "review"
else:
    print("Unsupported event type:", GITHUB_EVENT_NAME)
    exit(0)

# ------------------------------
# Skip comments not mentioning @ai or from bot itself
# ------------------------------
if "@ai" not in comment_body.lower():
    print("Skipping comment — @ai not mentioned.")
    exit(0)

if comment_user == BOT_USERNAME:
    print("Skipping bot's own comment.")
    exit(0)

# ------------------------------
# Generate AI reply
# ------------------------------
prompt = f"""
You are an AI code review assistant on GitHub. Someone mentioned you in a comment:

User: {comment_body}

Write a helpful, friendly, and concise response. Format it as Markdown.
"""
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    max_tokens=500,
    messages=[
        {"role": "system", "content": "You are a helpful AI code reviewer."},
        {"role": "user", "content": prompt}
    ]
)

ai_reply = response.choices[0].message.content
print("=== AI Reply ===")
print(ai_reply)

# ------------------------------
# Post reply
# ------------------------------
if comment_type == "general":
    # General PR conversation comment → create a new comment mentioning user
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
    data = {"body": f"@{comment_user} {ai_reply}"}
elif comment_type == "review":
    # PR review line comment → threaded reply
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/pulls/comments"
    data = {"body": ai_reply, "in_reply_to": int(comment_id)}

headers = {"Authorization": f"token {GITHUB_TOKEN}"}
resp = requests.post(url, json=data, headers=headers)

if resp.status_code in [200, 201]:
    print("✅ AI reply posted successfully")
else:
    print(f"❌ Failed to reply: {resp.status_code} - {resp.text}")