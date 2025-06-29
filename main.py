# main.py
import os
import uuid
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse

# Import the Celery task and database functions
from worker import process_report_task
from database import create_analysis_task, get_analysis_task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Blood Test Report Analyser API")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Blood Test Report Analyser API is running"}

@app.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_blood_report(
    file: UploadFile = File(...),
    query: str = Form(default="Summarise my Blood Test Report")
):
    """
    Accepts a blood test report, saves it, and queues it for analysis.
    Returns a task ID for polling the result.
    """
    task_id = str(uuid.uuid4())
    file_id = str(uuid.uuid4())
    file_path = f"data/blood_test_report_{file_id}.pdf"
    
    try:
        # Create a directory to store uploaded files
        os.makedirs("data", exist_ok=True)
        
        # Save the uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ensure query is not empty
        if not query or not query.strip():
            query = "Summarise my Blood Test Report"
            
        # 1. Create a record in the database
        create_analysis_task(task_id, file_name=file.filename, query=query)
        logging.info(f"Task {task_id} created for file: {file.filename}")

        # 2. Enqueue the background task with Celery
        process_report_task.delay(task_id, file_path, query)
        logging.info(f"Task {task_id} queued for processing.")
        
        return {
            "message": "Analysis has been started. Please check the result later.",
            "task_id": task_id,
            "status_endpoint": f"/result/{task_id}"
        }
        
    except Exception as e:
        logging.error(f"Error in /analyze endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/result/{task_id}")
async def get_analysis_result(task_id: str):
    """
    Fetches the status and result of an analysis task by its ID.
    """
    task = get_analysis_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = {
        "task_id": task["_id"],
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }
    
    if task["status"] == "COMPLETED":
        response["analysis"] = task.get("result")
    elif task["status"] == "FAILED":
        response["error"] = task.get("result")
        
    return JSONResponse(content=response)