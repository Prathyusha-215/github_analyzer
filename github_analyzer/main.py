import concurrent.futures
import logging
import time
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from config import CONFIG, validate_config
from excel_reader import read_students_file, extract_username, extract_user_and_repo
from github_fetcher import get_latest_repo_by_keywords, get_notebook_file
from notebook_parser import parse_notebook_from_url
from llm_analyzer import analyze_code_with_llm
from excel_writer import parse_llm_response, write_evaluation_file

# Configure logging
logging.basicConfig(filename='logs.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_student(student):
    """
    Process a single student: fetch repo, parse notebook, analyze, and return result.
    """
    name = student.get("name of the student")
    github_url = student.get("github link")
    
    result = {
        "Student": name,
        "GitHub Link": github_url,
        "Repo Found": "No",
        "Notebook Found": "No",
        "Notebook Type": "",
        "Overall Rating": "",
        "Positives": "",
        "Negatives": "",
        "Improvements": "",
        "Status": "Failed"
    }
    
    try:
        username, repo_name = extract_user_and_repo(github_url)
        if not username:
             raise ValueError("Invalid GitHub URL")

        # If repo_name is provided, try to fetch that specific repo
        if repo_name:
            from github_fetcher import get_github_client
            g = get_github_client()
            user = g.get_user(username)
            repo = user.get_repo(repo_name)
        else:
            repo = get_latest_repo_by_keywords(username, CONFIG['REPO_KEYWORDS'])

        if not repo:
            if CONFIG['REPO_KEYWORDS']:
                keywords_str = ', '.join(CONFIG['REPO_KEYWORDS'])
                logging.warning(f"No repository found with keywords [{keywords_str}] for {name}")
                result["Status"] = f"No Repository with Keywords"
            else:
                logging.warning(f"No repositories found for {name}")
                result["Status"] = f"No Repositories Found"
            return result

        result["Repo Found"] = repo.name
        
        notebook_file = get_notebook_file(repo)
        if not notebook_file:
            logging.warning(f"No notebook found in {repo.name} for {name}")
            result["Status"] = "No Notebook"
            return result
            
        result["Notebook Found"] = notebook_file.name
        
        # Check if download_url is available
        if not notebook_file.download_url:
             logging.warning(f"No download URL for notebook in {repo.name}")
             result["Status"] = "No Download URL"
             return result

        logging.info(f"Downloading notebook for {name}...")
        notebook_text = parse_notebook_from_url(notebook_file.download_url)
        
        logging.info(f"Analyzing notebook for {name}...")
        analysis = analyze_code_with_llm(notebook_text)
        
        parsed_feedback = parse_llm_response(analysis)
        result.update(parsed_feedback)
        result["Status"] = "Success"
        
        logging.info(f"Successfully processed {name}")
        
    except Exception as e:
        logging.error(f"Error processing {name}: {e}")
        result["Status"] = f"Error: {str(e)}"
        
    return result

def main():
    # Validate configuration
    validate_config()

    input_file = CONFIG['INPUT_FILE']
    output_file = CONFIG['OUTPUT_FILE']

    print(f"Starting GitHub Transaction Analyzer at {datetime.now()}")
    print(f"Searching for repositories with keywords: {CONFIG['REPO_KEYWORDS']}")
    print("Evaluating based on transaction analysis and business intelligence criteria")

    try:
        students = read_students_file(input_file)
    except Exception as e:
        print(f"Critical Error: {e}")
        return

    print(f"Found {len(students)} students. Starting analysis...")
    
    results = []
    
    # Using ThreadPoolExecutor for parallel processing
    # Adjust max_workers based on API rate limits and system capabilities
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS']) as executor:
        future_to_student = {executor.submit(process_student, student): student for student in students}

        # Progress bar for completion tracking
        with tqdm(total=len(students), desc="Analyzing students", unit="student") as pbar:
            for future in concurrent.futures.as_completed(future_to_student):
                student = future_to_student[future]
                try:
                    data = future.result()
                    results.append(data)
                    status = data['Status']
                    pbar.set_postfix({"Last": f"{student.get('name of the student', 'Unknown')} - {status}"})
                    pbar.update(1)
                except Exception as e:
                    print(f"Generated an exception for {student.get('name of the student', 'Unknown')}: {e}")
                    pbar.update(1)

            # Add delay between students to respect rate limits
            time.sleep(CONFIG['DELAY_BETWEEN_STUDENTS'])
                
    write_evaluation_file(results, output_file)
    print("Analysis complete. Check evaluation.xlsx and logs.txt.")

if __name__ == "__main__":
    main()
