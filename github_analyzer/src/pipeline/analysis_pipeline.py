from src.components.github_connector import GitHubConnector
from src.components.notebook_processor import NotebookProcessor
from src.components.llm_engine import LLMEngine
from src.components.report_generator import ReportGenerator
from src.utils.common import extract_user_and_repo, clean_github_url
from src.constants import Config
from src.logger.logging_config import setup_logging

logger = setup_logging()

class AnalysisPipeline:
    def __init__(self):
        self.github_connector = GitHubConnector()
        self.notebook_processor = NotebookProcessor()
        self.llm_engine = LLMEngine()
        self.report_generator = ReportGenerator()
        self.repo_keywords = Config.REPO_KEYWORDS

    def process_student(self, student, questions_content=None):
        """
        Process a single student: fetch repo, parse notebook, analyze, and return result.
        """
        # Debug logging to investigate missing keys
        logger.info(f"Processing student data: {student}")
        
        name = student.get("name of the student")
        github_url = student.get("github link")
        
        logger.info(f"Extracted - Name: {name}, GitHub URL: {github_url}")
        
        result = {
            "student_name": name,
            "github_link": github_url,
            "repo_found": "No",
            "notebook_found": "No",
            "notebook_type": "",
            "overall_rating": "",
            "mentor_comments": "",
            "status": "Failed"
        }
        
        github_url = clean_github_url(github_url)
        result["github_link"] = github_url
        
        try:
            username, repo_name = extract_user_and_repo(github_url)
            if not username:
                 raise ValueError("Invalid GitHub URL")

            # Fetch Repo
            if repo_name:
                try:
                    user = self.github_connector.g.get_user(username)
                    repo = user.get_repo(repo_name)
                except Exception:
                    repo = None
            else:
                repo = self.github_connector.get_latest_repo_by_keywords(username, self.repo_keywords)

            if not repo:
                if self.repo_keywords:
                    keywords_str = ', '.join(self.repo_keywords)
                    logger.warning(f"No repository found with keywords [{keywords_str}] for {name}")
                    result["status"] = f"No Repository with Keywords"
                else:
                    logger.warning(f"No repositories found for {name}")
                    result["status"] = f"No Repositories Found"
                return result

            result["repo_found"] = repo.name

            # Read ALL repo files instead of just the notebook
            logger.info(f"Reading entire repo contents for {name}...")
            repo_text = self.github_connector.get_repo_text_content(repo, max_chars=15000)

            if not repo_text:
                logger.warning(f"No readable content found in {repo.name} for {name}")
                result["status"] = "No Content Found"
                result["notebook_found"] = "No"
                result["mentor_comments"] = "No Readable Content Found in Repository"
                result["overall_rating"] = "N/A"
                return result

            result["notebook_found"] = "Yes (Repo Scan)"

            logger.info(f"Analyzing repo content for {name}...")
            analysis = self.llm_engine.analyze_code(repo_text, questions_content)
            
            parsed_feedback = self.report_generator.parse_llm_response(analysis)
            result.update(parsed_feedback)
            result["status"] = "Success"
            
            logger.info(f"Successfully processed {name}")
            
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            result["status"] = f"Error: {str(e)}"
            
        return result
