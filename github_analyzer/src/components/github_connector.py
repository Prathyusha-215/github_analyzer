from github import Github, GithubException
import time
from src.constants import Config
from src.logger.logging_config import setup_logging
from src.exceptions.custom_exceptions import RepoNotFoundError

logger = setup_logging()

# File extensions to collect content from
ANALYZABLE_EXTENSIONS = {
    '.py', '.ipynb', '.md', '.txt', '.js', '.ts', '.jsx', '.tsx',
    '.yaml', '.yml', '.json', '.toml', '.cfg', '.ini', '.env.example'
}
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', 'env', '.venv',
    'dist', 'build', '.idea', '.vscode', 'coverage', '.pytest_cache'
}


class GitHubConnector:
    def __init__(self):
        self.github_token = Config.GITHUB_TOKEN
        self.g = Github(self.github_token) if self.github_token else None

    def _check_rate_limit(self):
        """Check remaining API calls and wait if necessary."""
        if not self.g:
            raise ValueError("GITHUB_TOKEN not found in configuration")
        rate_limit = self.g.get_rate_limit()
        remaining = rate_limit.rate.remaining
        reset_time = rate_limit.rate.reset

        if remaining < 10:
            wait_time = (reset_time - time.time()) + 60
            if wait_time > 0:
                logger.warning(f"Rate limit low ({remaining} remaining). Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)

        return remaining

    # ------------------------------------------------------------------
    # Primary method: fetch repo directly from URL
    # ------------------------------------------------------------------

    def get_repo_by_url(self, github_url):
        """
        Fetches a GitHub repository object directly from a full URL.
        Supports: https://github.com/user/repo or github.com/user/repo
        """
        self._check_rate_limit()
        try:
            url = github_url.strip().rstrip('/')
            for prefix in ('https://', 'http://'):
                if url.startswith(prefix):
                    url = url[len(prefix):]
                    break

            parts = url.split('/')
            if len(parts) < 3 or 'github.com' not in parts[0]:
                raise ValueError(f"Invalid GitHub URL: {github_url}")

            username = parts[1]
            repo_name = parts[2]
            return self.g.get_repo(f"{username}/{repo_name}")
        except GithubException as e:
            logger.error(f"GitHub Error for URL {github_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching repo for URL {github_url}: {e}")
            return None

    # ------------------------------------------------------------------
    # Whole-repo file collector
    # ------------------------------------------------------------------

    def get_all_repo_files(self, repo, max_chars=15000):
        """
        Fetches content from the entire repository.
        Prioritizes: README > notebooks > Python/JS source > configs.

        Returns:
            tuple: (content_text: str, files_read: int, file_paths: list)
        """
        readme_files = []
        notebook_files = []
        source_files = []
        config_files = []

        def walk_tree(path="", depth=0):
            if depth > 5:
                return
            self._check_rate_limit()
            try:
                contents = repo.get_contents(path)
                if not isinstance(contents, list):
                    contents = [contents]
                for item in contents:
                    if item.type == "dir":
                        if item.name.lower() not in SKIP_DIRS:
                            walk_tree(item.path, depth + 1)
                    elif item.type == "file":
                        name_lower = item.name.lower()
                        ext = ('.' + name_lower.rsplit('.', 1)[-1]) if '.' in name_lower else ''

                        # Skip large and non-text files
                        if item.size > 80000:
                            continue
                        if ext not in ANALYZABLE_EXTENSIONS:
                            continue

                        if name_lower.startswith('readme'):
                            readme_files.append(item)
                        elif ext == '.ipynb':
                            notebook_files.append(item)
                        elif ext in {'.py', '.js', '.ts', '.jsx', '.tsx'}:
                            source_files.append(item)
                        else:
                            config_files.append(item)
            except Exception as e:
                logger.warning(f"Could not walk path '{path}': {e}")

        walk_tree()

        collected = []
        total_chars = 0
        files_read = 0
        file_paths = []  # Track names of analyzed files

        def read_item(item, label):
            nonlocal total_chars, files_read
            if total_chars >= max_chars:
                return
            try:
                content = item.decoded_content.decode('utf-8', errors='replace')
                snippet = content[:3000]  # Cap per-file at 3000 chars
                sep = '=' * 60
                entry = f"\n{sep}\n[{label}] {item.path}\n{sep}\n{snippet}\n"
                collected.append(entry)
                total_chars += len(entry)
                files_read += 1
                file_paths.append(item.path)  # Record the file path
            except Exception as e:
                logger.warning(f"Could not read {item.path}: {e}")

        # Prioritized collection
        for item in readme_files:
            read_item(item, "README")
        for item in notebook_files:
            read_item(item, "NOTEBOOK")
        for item in source_files:
            read_item(item, "SOURCE")
        for item in config_files:
            read_item(item, "CONFIG")

        logger.info(f"Collected {files_read} files ({total_chars} chars) from '{repo.name}'")
        return ''.join(collected), files_read, file_paths

    # ------------------------------------------------------------------
    # Legacy methods (kept for batch Excel mode)
    # ------------------------------------------------------------------

    def get_latest_repo_by_keywords(self, username, keywords=None):
        """Returns the latest (or keyword-matching) repo for a GitHub username."""
        self._check_rate_limit()
        try:
            user = self.g.get_user(username)
            repos = user.get_repos(sort="created", direction="desc")

            if not keywords or len(keywords) == 0:
                for repo in repos:
                    if not repo.archived and not repo.fork:
                        return repo
                return repos[0] if repos else None

            for repo in repos:
                repo_text = (repo.name + " " + (repo.description or "")).lower()
                if any(keyword.lower() in repo_text for keyword in keywords):
                    return repo
            return None
        except GithubException as e:
            logger.error(f"GitHub Error for user {username}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching repos for {username}: {e}")
            return None

    def get_notebook_file(self, repo):
        """
        Finds the first .ipynb file in the repository.
        Kept for backward compatibility with batch mode.
        """
        def search_contents(path="", depth=0, max_depth=2):
            if depth > max_depth:
                return None
            self._check_rate_limit()
            try:
                contents = repo.get_contents(path)
                for item in contents:
                    if item.type == "file" and item.name.endswith(".ipynb"):
                        return item
                    elif item.type == "dir" and depth < max_depth:
                        if item.name in ["", "notebooks", "src", "code", "project"]:
                            result = search_contents(item.path, depth + 1, max_depth)
                            if result:
                                return result
                return None
            except Exception as e:
                logger.error(f"Error searching {path} in {repo.name}: {e}")
                return None

        return search_contents()
