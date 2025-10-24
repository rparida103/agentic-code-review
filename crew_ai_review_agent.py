import os
from dotenv import load_dotenv
from openai import OpenAI
from crewai.agent import CrewAgent

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
agent = CrewAgent(model=MODEL, client=client)

# ------------------------------
# Step 1: List Python files in the PR
# ------------------------------
python_files = list_python_files(repo=GITHUB_REPO, pr_number=PR_NUMBER, token=GITHUB_TOKEN)

# ------------------------------
# Step 2: Review each Python file
# ------------------------------
for file_path in python_files:
    try:
        code = read_file(file_path)
        feedback = code_review(code)
        comment_status = post_comment(
            GITHUB_REPO,
            PR_NUMBER,
            f"**{file_path}**\n\n{feedback}",
            GITHUB_TOKEN,
        )
        print(f"Posted comment for {file_path}: {comment_status}")
    except Exception as e:
        print(f"Error reviewing {file_path}: {e}")
