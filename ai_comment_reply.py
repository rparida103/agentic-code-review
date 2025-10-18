import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
COMMENT_ID = os.getenv("COMMENT_ID")
COMMENT_BODY = os.getenv("COMMENT_BODY")
COMMENT_USER = os.getenv("COMMENT_USER")
BOT_USERNAME = os.getenv("BOT_USERNAME", "rparida103")  # your PAT account username

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Only respond if comment mentions @ai
# ------------------------------
if "@ai" not in COMMENT_BODY.lower():
    print("Skipping comment — does not mention @ai.")
    exit(0)

# Skip bot's own comments
if COMMENT_USER == BOT_USERNAME:
    print("Skipping bot's own comment.")
    exit(0)

# ------------------------------
# Generate AI reply
# ------------------------------
prompt = f"""
You are an AI code review assistant on GitHub. Someone mentioned you in a comment:

User: {COMMENT_BODY}

Write a helpful, friendly, and concise response. Format it as Markdown for GitHub.
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
# Post reply to the comment
# ------------------------------
url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/comments"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
data = {
    "body": ai_reply,
    "in_reply_to": int(COMMENT_ID)  # Threaded reply
}

resp = requests.post(url, json=data, headers=headers)
if resp.status_code == 201:
    print("✅ AI reply posted successfully")
else:
    print(f"❌ Failed to reply: {resp.status_code} - {resp.text}")