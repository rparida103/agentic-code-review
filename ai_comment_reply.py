import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

# ------------------------------
# Environment variables
# ------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT token
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")  # Path to event payload

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Load GitHub event payload
# ------------------------------
with open(GITHUB_EVENT_PATH, "r") as f:
    event = json.load(f)

# Determine event type
event_name = os.getenv("GITHUB_EVENT_NAME")

if event_name == "issue_comment":
    comment_id = event["comment"]["id"]
    comment_body = event["comment"]["body"]
    comment_user = event["comment"]["user"]["login"]
elif event_name == "pull_request_review_comment":
    comment_id = event["comment"]["id"]
    comment_body = event["comment"]["body"]
    comment_user = event["comment"]["user"]["login"]
else:
    print("Unsupported event type:", event_name)
    exit(0)

# ------------------------------
# Skip bot's own comments
# ------------------------------
BOT_USERNAME = os.getenv("BOT_USERNAME", "your-github-username")  # Set to PAT account login
if comment_user == BOT_USERNAME:
    print("Skipping bot's own comment.")
    exit(0)

# ------------------------------
# Generate AI reply
# ------------------------------
prompt = f"""
You are an AI code review assistant on GitHub. Someone replied to your previous comment:

User: {comment_body}

Write a helpful, friendly, and concise response. Format it as Markdown for GitHub.
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful AI code reviewer."},
        {"role": "user", "content": prompt}
    ]
)

ai_reply = response.choices[0].message.content
print("=== AI Reply ===")
print(ai_reply)

# ------------------------------
# Post reply to the comment
# ------------------------------
url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/comments"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
data = {
    "body": ai_reply,
    "in_reply_to": int(comment_id)  # Creates threaded reply
}

resp = requests.post(url, json=data, headers=headers)
if resp.status_code == 201:
    print("✅ AI reply posted successfully")
else:
    print(f"❌ Failed to reply: {resp.status_code} - {resp.text}")