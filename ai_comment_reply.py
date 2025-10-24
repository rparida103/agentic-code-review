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
GITHUB_TOKEN = os.getenv("GH_PAT")  # Personal access token
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
COMMENT_ID = os.getenv("COMMENT_ID")
COMMENT_BODY = os.getenv("COMMENT_BODY")
COMMENT_USER = os.getenv("COMMENT_USER")
BOT_USERNAME = os.getenv("BOT_USERNAME", "rparida103")  # Your bot username

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Only respond if comment mentions @ai_bot
# ------------------------------
if "@ai_bot" not in COMMENT_BODY.lower():
    print("Skipping comment — does not mention @ai_bot.")
    exit(0)

if COMMENT_USER == BOT_USERNAME:
    print("Skipping bot's own comment.")
    exit(0)

# ------------------------------
# Generate AI reply
# ------------------------------
prompt = f"""
You are an AI code assistant. Respond to the following GitHub comment politely and helpfully:

User: {COMMENT_BODY}
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    max_tokens=500,
    messages=[
        {"role": "system", "content": "You are a helpful AI code reviewer."},
        {"role": "user", "content": prompt},
    ]
)

ai_reply = response.choices[0].message.content
print("=== AI Reply ===")
print(ai_reply)

# ------------------------------
# Post reply to the comment
# ------------------------------
url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/comments"
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