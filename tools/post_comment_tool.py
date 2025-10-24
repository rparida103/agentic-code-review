import requests

def post_comment(repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a comment to the GitHub PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": body}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        return "Comment posted successfully"
    else:
        return f"Failed to comment: {response.status_code} - {response.text}"

tool_spec = {
    "type": "function",
    "function": {
        "name": "post_comment",
        "description": "Post a comment to the GitHub PR.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "pr_number": {"type": "integer"},
                "body": {"type": "string"},
                "token": {"type": "string"},
            },
            "required": ["repo", "pr_number", "body", "token"],
        },
    },
}