
import os
import shutil
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Import our new Async Pipeline and global TASKS store
from src.pipeline.async_pipeline import AsyncAnalysisPipeline, TASKS
from src.logger.logging_config import setup_logging
from src.constants import Config

# Setup logging
logger = setup_logging()
load_dotenv()

app = FastAPI(title="GitHub Repository Analyzer")

# Mount static files if you have them (e.g. css)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Templates
templates = Jinja2Templates(directory="templates")

# Initialize Pipeline Wrapper
async_pipeline = AsyncAnalysisPipeline()

# Ensure upload/output directories exist
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    students_file: UploadFile = File(...),
    questions_file: UploadFile = File(...),
    repo_keywords: Optional[str] = Form(None)
):
    """
    Handle file upload and start background analysis.
    """
    try:
        # Validate file types
        if not students_file.filename.endswith(('.xlsx', '.xls')):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Invalid students file. Please upload Excel."
            })
        
        # Save files
        task_id = str(uuid.uuid4())
        student_path = os.path.join(UPLOAD_DIR, f"{task_id}_{students_file.filename}")
        questions_path = os.path.join(UPLOAD_DIR, f"{task_id}_{questions_file.filename}")
        
        with open(student_path, "wb") as buffer:
            shutil.copyfileobj(students_file.file, buffer)
            
        with open(questions_path, "wb") as buffer:
            shutil.copyfileobj(questions_file.file, buffer)
            
        # Read questions content immediately
        with open(questions_path, "r", encoding="utf-8") as f:
            questions_content = f.read()

        # Parse keywords
        keywords_list = [k.strip() for k in repo_keywords.split(',')] if repo_keywords else None

        # Start Background Task
        # Note: We pass the method of our wrapper class
        background_tasks.add_task(
            async_pipeline.run_analysis_task,
            task_id,
            student_path,
            questions_content,
            OUTPUT_DIR,
            keywords_list
        )
        
        # Redirect to status page
        return RedirectResponse(url=f"/status-page/{task_id}", status_code=303)

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"Error starting analysis: {str(e)}"
        })

@app.get("/status-page/{task_id}", response_class=HTMLResponse)
async def status_page(request: Request, task_id: str):
    """Render the status page."""
    return templates.TemplateResponse("processing.html", {"request": request, "task_id": task_id})

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """JSON endpoint for polling status."""
    task = TASKS.get(task_id)
    if not task:
        return {"state": "NOT_FOUND", "progress": 0, "message": "Task not found"}
    return task

@app.get("/results/{task_id}", response_class=HTMLResponse)
async def results_page(request: Request, task_id: str):
    """Render the final results."""
    task = TASKS.get(task_id)
    if not task or task.get("state") != "COMPLETED":
         return RedirectResponse(url=f"/status-page/{task_id}")
    
    # Calculate stats for the template
    results = task.get("results", [])
    total = len(results)
    successful = sum(1 for r in results if r.get('status') == 'Success')
    success_rate = round((successful / total * 100), 1) if total > 0 else 0
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "results": results,
        "total_students": total,
        "successful": successful,
        "success_rate": success_rate,
        "output_filename": task.get("output_file"),
        "processing_info": "Analysis completed via Background Task."
    })

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download the generated report."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
