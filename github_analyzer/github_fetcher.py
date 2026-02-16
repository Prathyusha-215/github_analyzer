from github import Github, GithubException
import os
import time
from dotenv import load_dotenv

load_dotenv()

def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    return Github(token)

def check_rate_limit(g):
    """Check remaining API calls and wait if necessary"""
    rate_limit = g.get_rate_limit()
    remaining = rate_limit.rate.remaining
    reset_time = rate_limit.rate.reset
    
    if remaining < 10:  # Buffer for safety
        wait_time = (reset_time - time.time()) + 60  # Add 1 minute buffer
        if wait_time > 0:
            print(f"Rate limit low ({remaining} remaining). Waiting {wait_time:.0f} seconds...")
            time.sleep(wait_time)
    
    return remaining

def get_latest_repo_by_keywords(username, keywords=None):
    """
    Finds the latest repository containing any of the specified keywords in name or description.
    If no keywords provided, returns the most recent repository.
    Returns the Repository object or None.
    
    Args:
        username: GitHub username
        keywords: List of keywords to search for (default: None - returns most recent repo)
    """
    g = get_github_client()
    check_rate_limit(g)
    
    try:
        user = g.get_user(username)
        repos = user.get_repos(sort="created", direction="desc")
        
        # If no keywords specified, return the most recent repository
        if not keywords or len(keywords) == 0:
            for repo in repos:
                # Skip archived/forked repos unless they're the only option
                if not repo.archived and not repo.fork:
                    return repo
            # If no non-archived repos, return the most recent one
            return repos[0] if repos else None
        
        # Search for repositories matching keywords
        for repo in repos:
            repo_text = (repo.name + " " + (repo.description or "")).lower()
            if any(keyword.lower() in repo_text for keyword in keywords):
                return repo
        return None
    except GithubException as e:
        print(f"GitHub Error for user {username}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching repos for {username}: {e}")
        return None

# Backward compatibility
def get_latest_pandas_repo(username):
    """Legacy function - use get_latest_repo_by_keywords instead"""
    return get_latest_repo_by_keywords(username, ['pandas'])

def get_notebook_file(repo):
    """
    Finds the first .ipynb file in the repository (limited depth search).
    Returns the file content object or None.
    """
    g = get_github_client()
    
    def search_contents(path="", depth=0, max_depth=2):
        """Recursive search with depth limit"""
        if depth > max_depth:
            return None
            
        check_rate_limit(g)
        try:
            contents = repo.get_contents(path)
            for item in contents:
                if item.type == "file" and item.name.endswith(".ipynb"):
                    return item
                elif item.type == "dir" and depth < max_depth:
                    # Search in common directories first
                    if item.name in ["", "notebooks", "src", "code", "project"]:
                        result = search_contents(item.path, depth + 1, max_depth)
                        if result:
                            return result
            return None
        except Exception as e:
            print(f"Error searching {path} in {repo.name}: {e}")
            return None
    
    return search_contents()
