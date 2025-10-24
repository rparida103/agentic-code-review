import os
from dotenv import load_dotenv
from openai import OpenAI
from crewai.agent import Agent

from tools.list_files_tool import list_python_files
from tools.read_file_tool import read_file
from tools.code_review_tool import code_review
from tools.post_comment_tool import post_comment

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER", "0"))

MODEL = "gpt-4o-mini"

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Create CrewAgent
# ------------------------------
agent = Agent(
    model=MODEL,
    client=client,
    role="code reviewer",
    goal="Review Python files in the pull request and provide constructive feedback",
    backstory="An AI assistant specialized in code review to help improve code quality and maintainability."
)

# ------------------------------
# Register tools
# ------------------------------
tools = {
    "list_python_files": lambda: list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN),
    "read_file": read_file,
    "code_review": code_review,
    "post_comment": lambda file_path, feedback: post_comment(
        GITHUB_REPO,
        PR_NUMBER,
        f"**{file_path}**\n\n{feedback}",
        GITHUB_TOKEN,
    ),
}

# ------------------------------
# Run agent with tools using chat method
# ------------------------------
# Execute the agent autonomously with tools
agent_response = agent(
    goal="Review Python files in the pull request and provide constructive feedback",
    tools=tools
)

# Check if the agent returned a tool call
function_call = agent_response.get("function_call")
if function_call:
    tool_name = function_call["name"]
    arguments = function_call.get("arguments", {})
    if isinstance(arguments, str):
        import json
        arguments = json.loads(arguments)
    result = tools[tool_name](**arguments)
    agent.feed_result(result)
