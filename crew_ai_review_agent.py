import os
from dotenv import load_dotenv
from openai import OpenAI
from crewai.agent import Agent
from crewai.task import Task
from crewai.crew import Crew
from crewai.tools import tool

# Import your existing tools
from py_tools.list_files_tool import list_python_files
from py_tools.read_file_tool import read_file
from py_tools.code_review_tool import code_review
from py_tools.post_comment_tool import post_comment

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
# Crew Tool (used only for reasoning)
# ------------------------------
@tool
def list_pr_python_files_tool():
    """Lists all Python files modified in the PR (used by Crew for reasoning)."""
    return list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

# ------------------------------
# Normal Python functions for execution
# ------------------------------
def get_pr_python_files():
    """Return list of Python files (direct Python call)."""
    return list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

def read_file_content(file_path: str):
    return read_file(file_path)

def generate_code_review(file_content: str):
    return code_review(file_content)

def post_review_feedback(file_path: str, feedback: str):
    body = f"**{file_path}**\n\n{feedback}"
    return post_comment(repo=GITHUB_REPO, pr_number=PR_NUMBER, body=body, token=GITHUB_TOKEN)

# ------------------------------
# Create Crew Agent
# ------------------------------
code_reviewer_agent = Agent(
    model=MODEL,
    config={"client": client},
    role="Senior Code Reviewer",
    goal="Review Python files in the pull request and provide constructive feedback",
    backstory="An expert AI assistant specialized in code review.",
    tools=[list_pr_python_files_tool],  # Crew uses this tool for reasoning
)

# ------------------------------
# Define Crew Task
# ------------------------------
review_task = Task(
    description=f"""
        1. Use `list_pr_python_files_tool` to determine the Python files in PR #{PR_NUMBER}.
        2. For each file, read content, generate code review, and post feedback.
        3. Return a summary of all files reviewed.
    """,
    expected_output="Confirmation that comments were posted for all files.",
    agent=code_reviewer_agent,
)

# ------------------------------
# Run Crew (reasoning)
# ------------------------------
crew = Crew(
    agents=[code_reviewer_agent],
    tasks=[review_task],
    verbose=True,
)

print("Starting Crew AI Code Review (reasoning)...")
crew.kickoff()

# ------------------------------
# Execute real reviews and post comments
# ------------------------------
python_files = get_pr_python_files()  # Direct Python call
for file_path in python_files:
    content = read_file_content(file_path)
    feedback = generate_code_review(content)
    post_review_feedback(file_path, feedback)

print("\n✅ All Python files reviewed and comments posted to the PR.")