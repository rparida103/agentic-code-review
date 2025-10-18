from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import json

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")  # e.g. "rparida103/agentic-code-review"
PR_NUMBER = os.getenv("PR_NUMBER")     # we'll pass this in workflow

def review_code(file_path):
    with open(file_path, "r") as f:
        code = f.read()

    prompt = f"""
    You are a principal software engineer reviewing a pull request.
    Review the following Python code for:
    - Bugs and logic issues
    - Performance or security problems
    - Readability and maintainability
    - Testing suggestions

    Respond with concise, line-specific comments if possible.

    CODE:
    {code}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful AI code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    review_text = response.choices[0].message.content
    print("=== AI Code Review ===")
    print(review_text)
    return review_text


def post_comment_to_pr(review_text):
    if not all([GITHUB_TOKEN, REPO, PR_NUMBER]):
        print("Missing GitHub context — skipping PR comment.")
        return

    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {"body": f"🤖 **AI Code Review Feedback:**\n\n{review_text}"}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        print(f"✅ Comment added to PR #{PR_NUMBER}")
    else:
        print(f"⚠️ Failed to post comment: {response.status_code} - {response.text}")


if __name__ == "__main__":
    review_output = review_code("app.py")
    post_comment_to_pr(review_output)