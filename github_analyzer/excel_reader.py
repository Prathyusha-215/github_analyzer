import pandas as pd
import os
import re
from typing import List, Dict, Tuple

def read_students_file(file_path):
    """
    Reads the student Excel file and returns a list of dictionaries.
    Automatically detects columns for student names and GitHub URLs.
    Removes duplicates and handles various column naming conventions.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        df = pd.read_excel(file_path)

        # Remove completely empty rows
        df = df.dropna(how='all')

        # Detect columns
        name_col, github_col = detect_columns(df)

        if not name_col or not github_col:
            available_cols = list(df.columns)
            raise ValueError(f"Could not automatically detect required columns. Available columns: {available_cols}. "
                           f"Expected columns containing student names and GitHub URLs.")

        # Extract only the required columns and rename them
        df_clean = df[[name_col, github_col]].copy()
        df_clean.columns = ['name of the student', 'github link']

        # Remove rows with missing values in either column
        df_clean = df_clean.dropna(subset=['name of the student', 'github link'])

        # Convert to string and clean data
        df_clean['name of the student'] = df_clean['name of the student'].astype(str).str.strip()
        df_clean['github link'] = df_clean['github link'].astype(str).str.strip()

        # Remove empty strings
        df_clean = df_clean[
            (df_clean['name of the student'] != '') &
            (df_clean['github link'] != '')
        ]

        # Remove duplicates based on both name and GitHub link
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['name of the student', 'github link'], keep='first')
        duplicates_removed = initial_count - len(df_clean)

        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate entries")

        # Validate GitHub URLs
        df_clean['github link'] = df_clean['github link'].apply(clean_github_url)

        # Remove invalid GitHub URLs
        valid_github_mask = df_clean['github link'].apply(is_valid_github_url)
        invalid_count = len(df_clean) - valid_github_mask.sum()
        df_clean = df_clean[valid_github_mask]

        if invalid_count > 0:
            print(f"Removed {invalid_count} entries with invalid GitHub URLs")

        final_count = len(df_clean)
        print(f"Successfully processed {final_count} student entries")

        return df_clean.to_dict("records")

    except Exception as e:
        raise Exception(f"Error reading Excel file: {e}")

def detect_columns(df) -> Tuple[str, str]:
    """
    Automatically detects columns containing student names and GitHub URLs.
    Returns (name_column, github_column) or (None, None) if not found.
    """
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Possible name column patterns
    name_patterns = [
        r'.*name.*', r'.*student.*', r'.*user.*', r'.*person.*',
        r'full.?name', r'first.?name', r'last.?name', r'student.?name'
    ]

    # Possible GitHub column patterns
    github_patterns = [
        r'.*github.*', r'.*repo.*', r'.*link.*', r'.*url.*',
        r'.*profile.*', r'.*account.*', r'git.*link'
    ]

    name_col = None
    github_col = None

    # Find name column
    for col in df.columns:
        for pattern in name_patterns:
            if re.search(pattern, col, re.IGNORECASE):
                name_col = col
                break
        if name_col:
            break

    # Find GitHub column
    for col in df.columns:
        for pattern in github_patterns:
            if re.search(pattern, col, re.IGNORECASE):
                github_col = col
                break
        if github_col:
            break

    # If pattern matching fails, try content-based detection
    if not name_col:
        name_col = detect_name_column_by_content(df)
    if not github_col:
        github_col = detect_github_column_by_content(df)

    return name_col, github_col

def detect_name_column_by_content(df) -> str:
    """
    Detects name column by analyzing the content of columns.
    """
    for col in df.columns:
        if col in ['name of the student', 'github link']:  # Skip already identified columns
            continue

        sample_values = df[col].dropna().astype(str).head(10)

        # Check if values look like names (contain letters, possibly spaces)
        name_like_count = 0
        for value in sample_values:
            value = value.strip()
            if (len(value) > 1 and len(value) < 50 and
                re.search(r'[a-zA-Z]', value) and
                not re.search(r'https?://', value) and
                not re.search(r'\d{4,}', value)):  # Avoid URLs and long numbers
                name_like_count += 1

        if name_like_count >= len(sample_values) * 0.7:  # 70% of samples look like names
            return col

    return None

def detect_github_column_by_content(df) -> str:
    """
    Detects GitHub column by analyzing the content of columns.
    """
    for col in df.columns:
        if col in ['name of the student', 'github link']:  # Skip already identified columns
            continue

        sample_values = df[col].dropna().astype(str).head(10)

        # Check if values look like GitHub URLs
        github_like_count = 0
        for value in sample_values:
            value = value.strip()
            if (re.search(r'github\.com', value, re.IGNORECASE) or
                re.search(r'githubusercontent\.com', value, re.IGNORECASE) or
                (len(value) > 10 and '/' in value and not value.startswith('http'))):  # username/repo format
                github_like_count += 1

        if github_like_count >= len(sample_values) * 0.6:  # 60% of samples look like GitHub links
            return col

    return None

def clean_github_url(url: str) -> str:
    """
    Cleans and standardizes GitHub URLs.
    """
    if not url or pd.isna(url):
        return ""

    url = str(url).strip()

    # Handle various GitHub URL formats
    if url.startswith('http'):
        # Full URL
        pass
    elif url.startswith('github.com/'):
        url = 'https://' + url
    elif '/' in url and len(url.split('/')) == 2:
        # username/repo format
        url = f'https://github.com/{url}'
    elif not url.startswith('http') and len(url) > 0:
        # Assume it's a username
        url = f'https://github.com/{url}'

    # Remove trailing slashes and common suffixes
    url = url.rstrip('/')
    url = re.sub(r'/tree/.*$', '', url)  # Remove branch/tree paths
    url = re.sub(r'/blob/.*$', '', url)  # Remove file paths

    return url

def is_valid_github_url(url: str) -> bool:
    """
    Validates if a string is a valid GitHub URL or username.
    """
    if not url or pd.isna(url):
        return False

    url = str(url).strip()

    # Check for valid GitHub URL patterns
    github_patterns = [
        r'^https?://github\.com/[a-zA-Z0-9_-]+/?$',
        r'^https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+/?$',
        r'^[a-zA-Z0-9_-]+$',  # Just username
        r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+$',  # username/repo
    ]

    return any(re.match(pattern, url) for pattern in github_patterns)

def extract_user_and_repo(github_url):
    """
    Extracts (username, repo_name) from a GitHub URL or string.
    Returns (username, repo_name) or (username, None) if only username is present.
    Handles:
      - https://github.com/username
      - https://github.com/username/repo
      - username
      - username/repo
    """
    if not github_url or pd.isna(github_url):
        return (None, None)
    url = str(github_url).strip().rstrip('/')
    # Remove protocol if present
    url = re.sub(r'^https?://', '', url)
    # Remove github.com if present
    url = re.sub(r'^github\.com/', '', url, flags=re.IGNORECASE)
    parts = url.split('/')
    if len(parts) == 1:
        return (parts[0], None)
    elif len(parts) >= 2:
        return (parts[0], parts[1])
    return (None, None)

def extract_username(github_url):
    """
    Extracts the username from a GitHub URL or string.
    Handles both user and repo URLs.
    Example: https://github.com/john123 -> john123
             https://github.com/john123/repo -> john123
    """
    username, _ = extract_user_and_repo(github_url)
    return username
