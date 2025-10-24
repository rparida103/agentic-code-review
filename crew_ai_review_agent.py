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
# Tools as @tool for Crew reasoning
# ------------------------------
@tool
def list_pr_python_files():
    """Return a list of Python files modified in the PR."""
    return list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

# Other tools are normal Python functions to ensure actual PR posting
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
    goal="Review Python files in the pull request and post constructive feedback.",
    backstory="An expert AI assistant specialized in code review.",
    tools=[list_pr_python_files],  # only Crew uses this tool for reasoning
)

# ------------------------------
# Define Task
# ------------------------------
review_task = Task(
    description=f"""
        1. Use `list_pr_python_files` to get all Python files in PR #{PR_NUMBER}.
        2. For each file, read its content using Python directly.
        3. Generate detailed code review feedback using Python directly.
        4. Post review feedback to the PR using Python directly.
        5. Return a summary of all files reviewed.
    """,
    expected_output="Confirmation that comments were posted for all files.",
    agent=code_reviewer_agent,
)

# ------------------------------
# Run Crew
# ------------------------------
crew = Crew(
    agents=[code_reviewer_agent],
    tasks=[review_task],
    verbose=True,
)

print("Starting Crew AI Code Review...")
review_result = crew.kickoff()

# ------------------------------
# Step: actual review posting (bypassing Crew placeholder)
# ------------------------------
python_files = list_pr_python_files()
for file_path in python_files:
    content = read_file_content(file_path)
    feedback = generate_code_review(content)  # actual detailed review
    post_review_feedback(file_path, feedback)  # posts real comment to PR

print("\n--- Review Summary ---")
print(review_result)