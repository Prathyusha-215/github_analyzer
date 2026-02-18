from src.components.github_connector import GitHubConnector
from src.components.notebook_processor import NotebookProcessor
from src.components.llm_engine import LLMEngine
from src.components.report_generator import ReportGenerator
from src.utils.common import extract_user_and_repo
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
            "positives": "",
            "negatives": "",
            "improvements": "",
            "status": "Failed"
        }
        
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
            
            # Find Notebook
            notebook_file = self.github_connector.get_notebook_file(repo)
            if not notebook_file:
                logger.warning(f"No notebook found in {repo.name} for {name}")
                result["status"] = "No Notebook"
                return result
                
            result["notebook_found"] = notebook_file.name
            
            # Check download URL
            if not notebook_file.download_url:
                 logger.warning(f"No download URL for notebook in {repo.name}")
                 result["status"] = "No Download URL"
                 return result

            logger.info(f"Downloading notebook for {name}...")
            notebook_text = self.notebook_processor.parse_notebook_from_url(notebook_file.download_url)
            
            logger.info(f"Analyzing notebook for {name}...")
            # analysis = self.llm_engine.analyze_code(notebook_text, questions_content) 
            # Note: keeping original call, just handling result update next
            analysis = self.llm_engine.analyze_code(notebook_text, questions_content)
            
            parsed_feedback = self.report_generator.parse_llm_response(analysis)
            result.update(parsed_feedback)
            result["status"] = "Success"
            
            logger.info(f"Successfully processed {name}")
            
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            result["status"] = f"Error: {str(e)}"
            
        return result
