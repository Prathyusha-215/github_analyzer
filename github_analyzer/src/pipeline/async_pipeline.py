
import asyncio
import logging
import time
from typing import Dict, List
from datetime import datetime
import os
import shutil

# Import existing synchronous components
from src.pipeline.analysis_pipeline import AnalysisPipeline
from src.components.report_generator import ReportGenerator
from src.components.data_ingestion import DataIngestion
from src.logger.logging_config import setup_logging

logger = setup_logging()

# In-memory task store (Dictionary)
# Key: task_id (str)
# Value: Dict with keys: state, progress, message, result_path, error
TASKS: Dict[str, Dict] = {}

class AsyncAnalysisPipeline:
    def __init__(self):
        self.pipeline = AnalysisPipeline()
        self.data_ingestion = DataIngestion()
        self.report_generator = ReportGenerator()
    
    def run_analysis_task(self, task_id: str, students_path: str, questions_content: str, output_folder: str, repo_keywords: List[str] = None):
        """
        Runs the full analysis pipeline synchronously but updates the global TASKS dict.
        This function is meant to be run in a background thread by FastAPI.
        """
        logger.info(f"Starting background task {task_id}")
        TASKS[task_id] = {
            "state": "PROCESSING",
            "progress": 0,
            "message": "Initializing...",
            "results": None,
            "output_file": None,
            "error": None
        }

        try:
            # Update keywords if provided
            if repo_keywords is not None:
                from src.constants import Config
                Config.REPO_KEYWORDS = repo_keywords
            
            # 1. Read Students
            TASKS[task_id]["message"] = "Reading student data..."
            TASKS[task_id]["progress"] = 5
            
            try:
                students = self.data_ingestion.read_students_file(students_path)
            except Exception as e:
                raise Exception(f"Failed to read students file: {str(e)}")
            
            total_students = len(students)
            if total_students == 0:
                raise Exception("No students found in the uploaded file.")
            
            TASKS[task_id]["message"] = f"Found {total_students} students. Starting analysis..."
            TASKS[task_id]["progress"] = 10
            
            # 2. Process Students
            results = []
            for i, student in enumerate(students):
                # Calculate progress: 10% to 90%
                progress_start = 10
                progress_end = 90
                # Avoid division by zero
                current_percent = progress_start + (i / max(total_students, 1)) * (progress_end - progress_start)
                
                TASKS[task_id]["progress"] = current_percent
                TASKS[task_id]["message"] = f"Processing {i+1}/{total_students}: {student.get('name of the student', 'Unknown')}"
                
                # Sync Call
                try:
                    result = self.pipeline.process_student(student, questions_content)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Critical error processing student {i}: {e}")
                    results.append({
                        "student_name": student.get("name of the student", "Unknown"),
                        "status": "Failed",
                        "mentor_comments": str(e),
                        "repo_found": "No",
                        "notebook_found": "No"
                    })
            
            # 3. Generate Report
            TASKS[task_id]["message"] = "Generating Excel report..."
            TASKS[task_id]["progress"] = 95
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"evaluation_{timestamp}.xlsx"
            output_path = os.path.join(output_folder, output_filename)
            
            self.report_generator.write_evaluation_file(results, output_path)
            
            # 4. Finish
            TASKS[task_id]["state"] = "COMPLETED"
            TASKS[task_id]["progress"] = 100
            TASKS[task_id]["message"] = "Analysis Complete!"
            TASKS[task_id]["output_file"] = output_filename
            TASKS[task_id]["results"] = results # Store results for display
            
            logger.info(f"Task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            TASKS[task_id]["state"] = "FAILED"
            TASKS[task_id]["error"] = str(e)
            TASKS[task_id]["message"] = f"Error: {str(e)}"
        
        finally:
            # Cleanup input files if needed
            # os.remove(students_path)
            # if questions_content_file...
            pass
