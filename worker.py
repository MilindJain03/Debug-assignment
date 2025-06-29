# worker.py
import os
import logging
from celery import Celery
from dotenv import load_dotenv
from crewai import Crew, Process

# Load environment variables
load_dotenv()
# print(f"--- DEBUG: Loaded REDIS_URL is: '{os.getenv('REDIS_URL')}' ---")

# Import your agents and tasks
from agents import verifier, doctor, nutritionist, exercise_specialist, compiler_agent
from task import verification, help_patients, nutrition_analysis, exercise_planning, compile_report_task
from database import update_analysis_task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Celery
celery_app = Celery(
    'tasks',
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True
)

@celery_app.task(name="process_report_task")
def process_report_task(task_id: str, file_path: str, query: str):
    """
    The Celery task that runs the full CrewAI analysis.
    """
    logging.info(f"Starting CrewAI task {task_id} for file: {file_path}")
    
    try:
        # Update status to PROCESSING
        update_analysis_task(task_id, status="PROCESSING")
        
        medical_crew = Crew(
            agents=[verifier, doctor, nutritionist, exercise_specialist, compiler_agent],
            tasks=[verification, help_patients, nutrition_analysis, exercise_planning, compile_report_task],
            process=Process.sequential,
            verbose=2
        )
        
        inputs = {'query': query.strip(), 'file_path': file_path}
        
        result = medical_crew.kickoff(inputs=inputs)
        
        logging.info(f"CrewAI task {task_id} completed successfully.")
        # Update status to COMPLETED with the result
        update_analysis_task(task_id, status="COMPLETED", result=str(result))
        
    except Exception as e:
        logging.error(f"Error in CrewAI task {task_id}: {e}", exc_info=True)
        # Update status to FAILED with the error message
        update_analysis_task(task_id, status="FAILED", result=str(e))
        
    finally:
        # Clean up the uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Cleaned up file: {file_path}")
            except OSError as e:
                logging.warning(f"Could not remove file {file_path}: {e}")