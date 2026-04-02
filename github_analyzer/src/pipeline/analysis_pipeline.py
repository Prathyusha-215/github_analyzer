from src.components.github_connector import GitHubConnector
from src.components.repo_processor import RepoProcessor
from src.components.llm_engine import LLMEngine
from src.components.report_generator import ReportGenerator
from src.utils.common import extract_user_and_repo
from src.constants import Config
from src.logger.logging_config import setup_logging

logger = setup_logging()


class AnalysisPipeline:
    def __init__(self):
        self.github_connector = GitHubConnector()
        self.repo_processor = RepoProcessor()
        self.llm_engine = LLMEngine()
        self.report_generator = ReportGenerator()

    def process_repo(self, github_url, user_context=None, label=None):
        """
        Process a single GitHub repository URL end-to-end:
          1. Fetch the repo object
          2. Collect all repo files → structured text
          3. Run LLM analysis
          4. Parse and return structured result dict

        Args:
            github_url: Full GitHub repository URL
            user_context: User-provided evaluation criteria / questions
            label: Optional display name (e.g. student name) for batch mode
        """
        logger.info(f"Processing repo: {github_url}")

        result = {
            "label": label or github_url,
            "github_link": github_url,
            "repo_found": "No",
            "files_analyzed": 0,
            "files_list": [],
            "overall_score": "",
            "category_scores": "",
            "key_strengths": "",
            "critical_issues": "",
            "task_completion": "",
            "summary": "",
            "status": "Failed"
        }

        try:
            # 1. Fetch repo
            repo = self.github_connector.get_repo_by_url(github_url)
            if not repo:
                result["status"] = "Repo Not Found"
                logger.warning(f"Could not fetch repo for URL: {github_url}")
                return result

            result["repo_found"] = repo.full_name

            # 2. Build repo content summary
            repo_text, files_read, file_paths = self.repo_processor.build_repo_summary(
                self.github_connector, repo
            )
            result["files_analyzed"] = files_read
            result["files_list"] = file_paths

            if not repo_text:
                result["status"] = "No Analyzable Content"
                logger.warning(f"No content collected from {repo.full_name}")
                return result

            # 3. Run LLM analysis
            logger.info(f"Analyzing {repo.full_name} ({files_read} files)...")
            analysis = self.llm_engine.analyze_repo(repo_text, user_context)

            # 4. Parse result
            parsed = self.report_generator.parse_llm_response(analysis)
            result.update(parsed)
            result["status"] = "Success"
            logger.info(f"Successfully analyzed {repo.full_name}")

        except Exception as e:
            logger.error(f"Error processing {github_url}: {e}")
            result["status"] = f"Error: {str(e)}"

        return result

    def process_student(self, student, user_context=None):
        """
        Backward-compatible wrapper for batch (Excel) mode.
        Maps old student dict format to process_repo().
        """
        name = student.get("name of the student", "Unknown")
        github_url = student.get("github link", "")

        logger.info(f"Processing student: {name}, URL: {github_url}")

        result = self.process_repo(github_url, user_context, label=name)

        # Map label → student_name for backward compat with report generator
        result["student_name"] = result.pop("label", name)
        return result
