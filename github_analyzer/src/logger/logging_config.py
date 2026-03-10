import logging
import os
import sys

def setup_logging(log_file_path="logs.txt"):
    """
    Configures logging to write to both a file and console.
    """
    if os.environ.get("VERCEL") == "1":
        log_file_path = "/tmp/logs.txt"
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("GitHubAnalyzer")
