import requests
from openai import OpenAI

def get_pr_details(repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR details from GitHub."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def update_pr_description(repo: str, pr_number: int, token: str, new_body: str) -> str:
    """Update the PR description field on GitHub."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {token}"}
    data = {"body": new_body}
    resp = requests.patch(url, json=data, headers=headers)
    if resp.status_code == 200:
        return "✅ PR description updated successfully"
    else:
        return f"❌ Failed to update PR description: {resp.status_code} - {resp.text}"

def generate_pr_description(client: OpenAI, changed_files: list[str], model: str = "gpt-4o-mini") -> str:
    """Generate a brief PR description using OpenAI based on changed files."""
    prompt = f"""
You are an AI assistant. A PR has the following changed Python files:

{changed_files}

Write a clear and concise pull request description (2-4 sentences) summarizing
the purpose and main changes of the PR. Make it suitable for the GitHub PR description field.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250
    )
    return response.choices[0].message.content.strip()