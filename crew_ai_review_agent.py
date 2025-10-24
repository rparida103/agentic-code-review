import os
from dotenv import load_dotenv
from openai import OpenAI
from crewai.agent import Agent
from crewai.task import Task
from crewai.crew import Crew
from crewai_tools import tool

# Import your custom tools (assumed to be standard functions)
from tools.list_files_tool import list_python_files
from tools.read_file_tool import read_file
from tools.code_review_tool import code_review
from tools.post_comment_tool import post_comment

# ------------------------------
# Load environment variables and setup
# ------------------------------
load_dotenv()

# Get environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER", "0"))

MODEL = "gpt-4o-mini"

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Define custom tools using the @tool decorator
# ------------------------------

@tool
def list_pr_python_files():
    """Lists all Python files modified in the current pull request. Returns a list of file paths."""
    return list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

@tool
def read_file(file_path: str):
    """Reads the content of a specified file path."""
    return read_file(file_path)

@tool
def code_review(file_content: str):
    """Provides a detailed code review for the given file content, focusing on quality, bugs, and best practices."""
    return code_review(file_content)

@tool
def post_review_comment(file_path: str, feedback: str):
    """Posts a comment to the pull request for a given file path with the review feedback."""
    body = f"**{file_path}**\n\n{feedback}"
    return post_comment(repo=GITHUB_REPO, pr_number=PR_NUMBER, body=body, token=GITHUB_TOKEN)

# List of Tool objects to be used by the agent
available_tools = [list_pr_python_files, read_file, code_review, post_review_comment]

# ------------------------------
# Create CrewAgent
# ------------------------------
code_reviewer_agent = Agent(
    model=MODEL,
    config={"client": client},
    role="Senior Code Reviewer",
    goal="Identify and post constructive feedback on all Python files modified in the pull request.",
    backstory="An expert AI assistant specialized in code review.",
    tools=available_tools,
)

# ------------------------------
# Define Task
# ------------------------------
review_task = Task(
    description=f"""
        1. Use `list_pr_python_files` to get a list of all modified Python files in Pull Request #{PR_NUMBER}.
        2. For each file, use `read_file` to get its content.
        3. Use `code_review` to analyze the file content and generate detailed feedback.
        4. Finally, use `post_review_comment` to post the feedback back to the pull request for the corresponding file.
        5. Your final answer must be a summary of the files reviewed and the action taken.
    """,
    expected_output="A confirmation message listing all files reviewed and indicating that comments were successfully posted to the pull request.",
    agent=code_reviewer_agent,
)

# ------------------------------
# Run Crew
# ------------------------------
code_review_crew = Crew(
    agents=[code_reviewer_agent],
    tasks=[review_task],
    verbose=0,
)

print("Starting Code Review Crew...")
review_result = code_review_crew.kickoff()

# ------------------------------
# Print final result
# ------------------------------
print("\n--- Review Summary ---")
print(review_result)