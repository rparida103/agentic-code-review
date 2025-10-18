import os
import requests
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
BOT_USERNAME = os.getenv("BOT_USERNAME", "rparida103")
PR_NUMBER = os.getenv("PR_NUMBER")

client = OpenAI(api_key=OPENAI_API_KEY)

time.sleep(5)
# ------------------------------
# Fetch all comments on the PR
# ------------------------------
url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
resp = requests.get(url, headers=headers)
comments = resp.json()

for c in comments:
    comment_id = c["id"]
    comment_body = c["body"]
    comment_user = c["user"]["login"]

    # Skip if not mentioning @ai or from the bot itself
    if "@ai" not in comment_body.lower() or comment_user == BOT_USERNAME:
        continue

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
    print(f"=== Replying to comment {comment_id} ===")
    print(ai_reply)

    # ------------------------------
    # Post reply as a new comment mentioning the user
    # ------------------------------
    data = {"body": f"@{comment_user} {ai_reply}"}
    post_resp = requests.post(url, json=data, headers=headers)

    if post_resp.status_code in [200, 201]:
        print(f"✅ Replied successfully to comment {comment_id}")
    else:
        print(f"❌ Failed to reply to comment {comment_id}: {post_resp.status_code} - {post_resp.text}")