# database.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
analysis_collection = db["analysis_tasks"]

def create_analysis_task(task_id: str, file_name: str, query: str):
    """Inserts a new task record into the database."""
    task_document = {
        "_id": task_id,
        "file_name": file_name,
        "query": query,
        "status": "PENDING",
        "result": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    analysis_collection.insert_one(task_document)
    return task_document

def get_analysis_task(task_id: str):
    """Retrieves a task record from the database."""
    return analysis_collection.find_one({"_id": task_id})

def update_analysis_task(task_id: str, status: str, result: str = None):
    """Updates the status and result of a task."""
    update_data = {
        "$set": {
            "status": status,
            "updated_at": datetime.utcnow()
        }
    }
    if result is not None:
        update_data["$set"]["result"] = result
        
    analysis_collection.update_one({"_id": task_id}, update_data)