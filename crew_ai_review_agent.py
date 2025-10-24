import os
from dotenv import load_dotenv
from openai import OpenAI
# Import necessary classes for CrewAI
from crewai.agent import Agent
from crewai.task import Task
from crewai.crew import Crew

# Import your custom tools
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
PR_NUMBER = int(os.getenv("PR_NUMBER", "0")) # Ensure it's an integer

MODEL = "gpt-4o-mini"

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# Define custom tools with arguments
# ------------------------------
# We wrap the tools that require environment variables to be passed
def list_pr_python_files():
    """Lists all Python files modified in the current pull request."""
    return list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

def post_review_comment(file_path: str, feedback: str):
    """Posts a comment to the pull request with review feedback."""
    return post_comment(
        repo=GITHUB_REPO,
        pr_number=PR_NUMBER,
        body=f"**{file_path}**\n\n{feedback}",
        token=GITHUB_TOKEN,
    )

# List of tools to be used by the agent
available_tools = [
    list_pr_python_files,
    read_file,
    code_review,
    post_review_comment
]

# ------------------------------
# Create CrewAgent
# ------------------------------
code_reviewer_agent = Agent(
    model=MODEL,
    # Use the client/config pattern for OpenAI in CrewAI
    config={"client": client},
    role="Senior Code Reviewer",
    goal="Identify and post constructive feedback on all Python files modified in the pull request for quality, maintainability, and best practices.",
    backstory="An expert AI assistant specialized in code review, dedicated to improving code quality and maintainability in collaborative projects.",
    tools=available_tools, # Pass tools directly to the Agent
    verbose=0, # Recommended for debugging and visibility
)

# ------------------------------
# Define Task
# ------------------------------
review_task = Task(
    description=f"""
        1. Use the `list_pr_python_files` tool to get a list of all modified Python files in Pull Request #{PR_NUMBER}.
        2. For each file, use the `read_file` tool to get its content.
        3. Use the `code_review` tool to analyze the file content and generate detailed, constructive feedback, focusing on bugs, security, style, and efficiency.
        4. Finally, for each file's feedback, use the `post_review_comment` tool to post the comment back to the pull request.
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
    verbose=0, # Increased verbosity shows all details
)

# Execute the crew
print("Starting Code Review Crew...")
review_result = code_review_crew.kickoff()

# ------------------------------
# Print final result
# ------------------------------
print("\n" + "="*50)
print("CREW EXECUTION FINISHED")
print("="*50)
print(review_result)