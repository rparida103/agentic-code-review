import os
from dotenv import load_dotenv
from openai import OpenAI
from crewai.agent import Agent
from crewai.task import Task
from crewai.crew import Crew
from crewai.tools import tool

# Import existing functions
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
# Define tools using @tool decorator
# ------------------------------
@tool
def list_pr_python_files():
    """Lists all Python files modified in the current pull request."""
    return list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

@tool
def read_file_content(file_path: str):
    """Reads the content of a specified file path."""
    return read_file(file_path)

@tool
def generate_code_review(file_content: str):
    """Analyzes Python code and generates review feedback."""
    return code_review(file_content)

@tool
def post_review_feedback(file_path: str, feedback: str):
    """Posts review feedback to the pull request for the specified file."""
    body = f"**{file_path}**\n\n{feedback}"
    return post_comment(repo=GITHUB_REPO, pr_number=PR_NUMBER, body=body, token=GITHUB_TOKEN)

# ------------------------------
# Create the Agent
# ------------------------------
code_reviewer_agent = Agent(
    model=MODEL,
    config={"client": client},
    role="Senior Code Reviewer",
    goal="Review Python files in the pull request and post constructive feedback.",
    backstory="An expert AI assistant specialized in code review.",
    tools=[list_pr_python_files, read_file_content, generate_code_review, post_review_feedback]
)

# ------------------------------
# Define Task
# ------------------------------
review_task = Task(
    description=f"""
        1. Use `list_pr_python_files` to get all Python files in PR #{PR_NUMBER}.
        2. For each file, call `read_file_content`.
        3. Call `generate_code_review` to analyze content.
        4. Call `post_review_feedback` to post the review.
        5. Final output should be a summary of all files reviewed and confirmation of posted comments.
    """,
    expected_output="Confirmation that comments were posted for all files.",
    agent=code_reviewer_agent
)

# ------------------------------
# Run Crew
# ------------------------------
crew = Crew(agents=[code_reviewer_agent], tasks=[review_task], verbose=True)
print("Starting Crew AI Code Review...")
review_result = crew.kickoff()

# ------------------------------
# Print final result
# ------------------------------
print("\n--- Review Summary ---")
print(review_result)