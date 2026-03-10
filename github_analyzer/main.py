
import os
import shutil
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from src.pipeline.async_pipeline import AsyncAnalysisPipeline, TASKS
from src.logger.logging_config import setup_logging
from src.constants import Config

logger = setup_logging()
load_dotenv()

app = FastAPI(title="GitHub Repository Analyzer")
templates = Jinja2Templates(directory="templates")

async_pipeline = AsyncAnalysisPipeline()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -----------------------------------------------------------------------
# Home
# -----------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------------------------------------------------
# Primary route — single-repo real-time analysis
# -----------------------------------------------------------------------

@app.post("/analyze-single")
async def analyze_single(
    request: Request,
    background_tasks: BackgroundTasks,
    github_url: str = Form(...),
    user_context: str = Form(""),
):
    """
    Start a real-time analysis for a single GitHub repository URL.
    Accepts the URL and user-provided evaluation context from the form.
    """
    try:
        github_url = github_url.strip()
        if not github_url or "github.com" not in github_url:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)."
            })

        task_id = str(uuid.uuid4())
        background_tasks.add_task(
            async_pipeline.run_single_repo_task,
            task_id,
            github_url,
            user_context,
            OUTPUT_DIR
        )
        return RedirectResponse(url=f"/status-page/{task_id}", status_code=303)

    except Exception as e:
        logger.error(f"Single-repo analysis failed: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error starting analysis: {str(e)}"
        })


# -----------------------------------------------------------------------
# Batch route — Excel file upload (legacy / classroom mode)
# -----------------------------------------------------------------------

@app.post("/analyze")
async def analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    students_file: UploadFile = File(...),
    user_context: str = Form(""),
    repo_keywords: Optional[str] = Form(None)
):
    """
    Batch analysis: upload an Excel file with student names & GitHub links,
    plus optional user-provided evaluation context.
    """
    try:
        if not students_file.filename.endswith(('.xlsx', '.xls')):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Invalid file. Please upload an Excel file (.xlsx or .xls)."
            })

        task_id = str(uuid.uuid4())
        student_path = os.path.join(UPLOAD_DIR, f"{task_id}_{students_file.filename}")

        with open(student_path, "wb") as buffer:
            shutil.copyfileobj(students_file.file, buffer)

        keywords_list = [k.strip() for k in repo_keywords.split(',')] if repo_keywords else None

        background_tasks.add_task(
            async_pipeline.run_analysis_task,
            task_id,
            student_path,
            user_context,
            OUTPUT_DIR,
            keywords_list
        )
        return RedirectResponse(url=f"/status-page/{task_id}", status_code=303)

    except Exception as e:
        logger.error(f"Batch upload failed: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error starting analysis: {str(e)}"
        })


# -----------------------------------------------------------------------
# Status & Results
# -----------------------------------------------------------------------

@app.get("/status-page/{task_id}", response_class=HTMLResponse)
async def status_page(request: Request, task_id: str):
    """Render the processing status page."""
    return templates.TemplateResponse("processing.html", {"request": request, "task_id": task_id})


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """JSON endpoint for polling task status."""
    task = TASKS.get(task_id)
    if not task:
        return {"state": "NOT_FOUND", "progress": 0, "message": "Task not found"}
    return task


@app.get("/results/{task_id}", response_class=HTMLResponse)
async def results_page(request: Request, task_id: str):
    """Render the final results page."""
    task = TASKS.get(task_id)
    if not task or task.get("state") != "COMPLETED":
        return RedirectResponse(url=f"/status-page/{task_id}")

    results = task.get("results", [])
    total = len(results)
    successful = sum(1 for r in results if r.get('status') == 'Success')
    success_rate = round((successful / total * 100), 1) if total > 0 else 0
    mode = task.get("mode", "batch")

    return templates.TemplateResponse("results.html", {
        "request": request,
        "results": results,
        "total_repos": total,
        "successful": successful,
        "success_rate": success_rate,
        "output_filename": task.get("output_file"),
        "mode": mode,
    })


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download the generated Excel report."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
