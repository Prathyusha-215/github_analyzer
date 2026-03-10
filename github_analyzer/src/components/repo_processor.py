import nbformat
from io import StringIO
from src.constants import Config
from src.logger.logging_config import setup_logging

logger = setup_logging()


class RepoProcessor:
    """
    Builds a structured text representation of an entire GitHub repository.
    Handles READMEs, Jupyter notebooks, Python/JS source, and config files.
    """

    def __init__(self):
        self.max_chars = Config.MAX_REPO_CHARS

    def parse_notebook_content(self, raw_content):
        """
        Parses raw .ipynb file content (string) into readable text.
        Extracts markdown and code cells up to a per-notebook character limit.
        """
        try:
            nb = nbformat.reads(raw_content, as_version=4)
            text = ""
            char_budget = 4000  # per-notebook budget

            for cell in nb.cells:
                if len(text) >= char_budget:
                    break
                if cell.cell_type == "markdown" and len(cell.source) < 600:
                    snippet = f"[MARKDOWN]\n{cell.source}\n\n"
                    text += snippet
                elif cell.cell_type == "code" and len(cell.source) < 2000:
                    snippet = f"[CODE]\n{cell.source}\n\n"
                    text += snippet

            return text[:char_budget]
        except Exception as e:
            logger.warning(f"Could not parse notebook content: {e}")
            return raw_content[:2000]

    def build_repo_summary(self, github_connector, repo):
        """
        Fetches all analyzable files from a repo and builds a structured
        summary string for the LLM.

        Returns:
            tuple: (repo_text: str, files_read: int, file_paths: list)
        """
        raw_content, files_read, file_paths = github_connector.get_all_repo_files(
            repo, max_chars=self.max_chars
        )

        if not raw_content:
            logger.warning(f"No content collected from repo '{repo.name}'")
            return "", 0, []

        stars = repo.stargazers_count
        language = repo.language or "Unknown"
        description = repo.description or "No description provided"

        header = (
            f"REPOSITORY: {repo.full_name}\n"
            f"Language: {language} | Stars: {stars}\n"
            f"Description: {description}\n"
            f"{'='*60}\n"
        )

        return header + raw_content, files_read, file_paths
