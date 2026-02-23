from src.utils.common import clean_github_url, extract_user_and_repo

test_urls = [
    "https://github.com/Nikitha0320/tekworks-datavisualization.git",
    "https://github.com/Nikitha0320/tekworks-datavisualization.git/",
    "https://github.com/user/repo.git",
    "https://github.com/user/repo",
    "https://github.com/user/repo/blob/main/file.ipynb",
    "https://github.com/user/repo/tree/master/folder"
]

for url in test_urls:
    cleaned = clean_github_url(url)
    user, repo = extract_user_and_repo(cleaned)
    print(f"Original: {url}")
    print(f"Cleaned:  {cleaned}")
    print(f"User/Repo: {user}/{repo}")
    print("-" * 20)
