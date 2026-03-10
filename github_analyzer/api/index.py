import sys
import os

# Add the github_analyzer folder to sys.path so we can import from it
analyzer_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, analyzer_dir)

from main import app
