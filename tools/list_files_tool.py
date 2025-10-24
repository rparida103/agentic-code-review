import requests

def list_python_files(repo: str, pr_number: int, token: str) -> list[str]:
    """Return list of Python files changed in the PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json()
    return [f["filename"] for f in files if f["filename"].endswith(".py")]

tool_spec = {
    "type": "function",
    "function": {
        "name": "list_python_files",
        "description": "Get all Python files changed in the PR.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "pr_number": {"type": "integer"},
                "token": {"type": "string"},
            },
            "required": ["repo", "pr_number", "token"],
        },
    },
}