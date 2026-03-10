import sys
import os

# Add the github_analyzer folder to sys.path so we can import from it
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
analyzer_dir = os.path.join(repo_root, "github_analyzer")
sys.path.insert(0, analyzer_dir)

from main import app
