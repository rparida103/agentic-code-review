def read_file(file_path: str) -> str:
    """Return the content of a local file."""
    with open(file_path, "r") as f:
        return f.read()

tool_spec = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read and return the content of a local file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
            },
            "required": ["file_path"],
        },
    },
}