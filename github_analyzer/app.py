from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile
from dotenv import load_dotenv

load_dotenv()

import config
CONFIG = config.CONFIG
validate_config = config.validate_config
from excel_reader import read_students_file, extract_username, extract_user_and_repo
from github_fetcher import get_latest_repo_by_keywords, get_notebook_file
from notebook_parser import parse_notebook_from_url
from llm_analyzer import analyze_code_with_llm
from excel_writer import parse_llm_response, write_evaluation_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'github-analyzer-secret-key-2024'
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if files are uploaded
        if 'students_file' not in request.files or 'questions_file' not in request.files:
            flash('Both students Excel file and questions text file are required', 'error')
            return redirect(request.url)

        students_file = request.files['students_file']
        questions_file = request.files['questions_file']

        if students_file.filename == '' or questions_file.filename == '':
            flash('Both files must be selected', 'error')
            return redirect(request.url)

        if not (allowed_file(students_file.filename) and allowed_file(questions_file.filename)):
            flash('Invalid file types. Please upload Excel (.xlsx/.xls) and text (.txt) files', 'error')
            return redirect(request.url)

        try:
            # Save uploaded files
            students_filename = secure_filename(students_file.filename)
            questions_filename = secure_filename(questions_file.filename)

            students_path = os.path.join(app.config['UPLOAD_FOLDER'], students_filename)
            questions_path = os.path.join(app.config['UPLOAD_FOLDER'], questions_filename)

            students_file.save(students_path)
            questions_file.save(questions_path)

            # Read questions content
            with open(questions_path, 'r', encoding='utf-8') as f:
                questions_content = f.read()

            # Update configuration from form
            repo_keywords = request.form.get('repo_keywords', '').strip()
            if repo_keywords:
                CONFIG['REPO_KEYWORDS'] = [k.strip() for k in repo_keywords.split(',') if k.strip()]
            else:
                CONFIG['REPO_KEYWORDS'] = []  # Empty list means analyze any repository


            # Validate configuration
            validate_config()

            # Read students with duplicate removal and column detection
            import io
            import sys

            # Capture print statements from read_students_file
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()

            try:
                students = read_students_file(students_path)
            finally:
                sys.stdout = old_stdout

            processing_info = captured_output.getvalue()

            # Process students with progress updates
            results = []
            for i, student in enumerate(students):
                result = process_student(student, questions_content)
                results.append(result)

            # Generate output
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"evaluation_{timestamp}.xlsx"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

            write_evaluation_file(results, output_path)

            # Calculate summary stats
            total_students = len(results)
            successful = sum(1 for r in results if r.get('Status') == 'Success')
            success_rate = (successful / total_students * 100) if total_students > 0 else 0

            return render_template('results.html',
                                 results=results,
                                 total_students=total_students,
                                 successful=successful,
                                 success_rate=round(success_rate, 1),
                                 output_filename=output_filename,
                                 processing_info=processing_info)

        except Exception as e:
            flash(f'Error processing files: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True, download_name=filename)

def process_student(student, questions_content):
    """Process a single student with dynamic questions"""
    name = student.get("name of the student")
    github_url = student.get("github link")

    result = {
        "Student": name,
        "GitHub Link": github_url,
        "Repo Found": "No",
        "Notebook Found": "No",
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
            result["Status"] = f"No Matching Repo"
            return result

        result["Repo Found"] = repo.name

        notebook_file = get_notebook_file(repo)
        if not notebook_file:
            result["Status"] = "No Notebook"
            return result

        result["Notebook Found"] = notebook_file.name

        if not notebook_file.download_url:
            result["Status"] = "No Download URL"
            return result

        notebook_text = parse_notebook_from_url(notebook_file.download_url)

        # Analyze with dynamic questions
        analysis = analyze_code_with_llm(notebook_text, questions_content)

        parsed_feedback = parse_llm_response(analysis)
        result.update(parsed_feedback)
        result["Status"] = "Success"

    except Exception as e:
        result["Status"] = f"Error: {str(e)}"

    return result

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)