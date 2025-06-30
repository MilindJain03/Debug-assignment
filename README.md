

# AI Internship Assignment - Blood Test Analysis System

This project is the completed submission for the VWO AI Internship Debug Challenge. The original codebase was non-functional due to a series of critical bugs. This repository contains the fully debugged and re-architected version, which is now a robust, scalable, and reliable service.

The system was not only fixed but was also significantly enhanced with bonus features, including an **asynchronous task queue** using **Celery and Redis** and a **MongoDB database** for persistence. This ensures the system can handle concurrent requests and maintain a history of all analyses.

This document details the bonus features implemented, the specific bugs that were found and fixed, and provides comprehensive instructions for setup, usage, and API interaction.

## Bonus Features Implemented

To elevate the system from a simple script to a production-ready service, the following bonus features were implemented.

### 1. Asynchronous Queue Worker Model
The original application was synchronous, meaning it would block and could only handle one request at a time, leading to API timeouts. To solve this, the system was re-architected with a queue worker model:
*   **Technology:** Celery (Task Queue) and Redis (Message Broker).
*   **Workflow:** The `/analyze` endpoint now instantly accepts an upload, creates a task record, and places the analysis job on a queue. It immediately returns a `task_id` to the user. A Celery worker process, running separately, picks up and executes the complex AI analysis in the background, ensuring the API remains responsive and can handle a high volume of concurrent requests.

### 2. Database Integration for Persistence
The original system was stateless, meaning analysis results were lost if the server restarted. To provide persistence and tracking, a database was integrated:
*   **Technology:** MongoDB.
*   **Workflow:** A new `database.py` module handles all data persistence. When a request comes in, a document is created in the database with a `PENDING` status. The Celery worker updates this status to `PROCESSING`, `COMPLETED`, or `FAILED` during the job's lifecycle. The final report or any error messages are saved to the database, allowing users to retrieve their results at any time via a new polling endpoint.

---
## Bugs Found and Fixes

The codebase was plagued by numerous bugs across all modules. Here is a detailed, file-by-file breakdown of the issues that were identified and resolved.

### `main.py` - Critical Issues Fixed

*   **Bug 1: Missing Agent Imports**
    *   **Problem:** Only one agent (`doctor`) and one task (`help_patients`) were imported, making a comprehensive analysis impossible.
    *   **Fix:** Imported all four specialized agents and their corresponding tasks to enable a full workflow.
        ```python
        # Before
        from agents import doctor
        from task import help_patients
        
        # After  
        from agents import doctor, verifier, nutritionist, exercise_specialist
        from task import help_patients, nutrition_analysis, exercise_planning, verification
        ```

*   **Bug 2: Incomplete Crew Configuration**
    *   **Problem:** The `Crew` was initialized with only a single agent and task, severely limiting its analytical capabilities.
    *   **Fix:** The `Crew` is now configured with the full team of four agents and their respective tasks.
        ```python
        # Before
        medical_crew = Crew(agents=[doctor], tasks=[help_patients])
        
        # After
        medical_crew = Crew(
            agents=[doctor, verifier, nutritionist, exercise_specialist],
            tasks=[verification, help_patients, nutrition_analysis, exercise_planning]
        )
        ```

*   **Bug 3: Missing File Path in Crew Inputs**
    *   **Problem:** The `Crew` was not receiving the file path of the uploaded PDF, so agents could not access the correct data.
    *   **Fix:** The unique `file_path` is now passed as a key-value pair in the `inputs` dictionary for the `crew.kickoff` method.
        ```python
        # Before
        result = medical_crew.kickoff({'query': query})
        
        # After
        result = medical_crew.kickoff(inputs={"query": query, "file_path": file_path})
        ```

### `agents.py` - Agent Configuration Issues

*   **Bug 1: Undefined LLM Variable**
    *   **Problem:** The line `llm = llm` caused a `NameError` because the variable was used before it was assigned.
    *   **Fix:** Implemented proper configuration for the Gemini LLM via LiteLLM, including API key validation.
        ```python
        # Before
        llm = llm  #  Undefined variable
        
        # After
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set!")
        llm = LLM(
            model="gemini/gemini-2.0-flash",
            temperature=0.7,
        )

        ```

*   **Bug 2: Incorrect Tool Import & Assignment**
    *   **Problem:** The code attempted to import a non-existent `BloodTestReportTool` class and then incorrectly referenced one of its methods.
    *   **Fix:** Changed the import to the correctly named `blood_pdf_tool` and assigned the tool variable directly to the agent's `tools` list.
        ```python
        # Before
        from tools import BloodTestReportTool
        doctor = Agent(..., tool=[BloodTestReportTool().read_data_tool])

        # After
        from tools import blood_pdf_tool
        doctor = Agent(..., tools=[blood_pdf_tool])
        ```

*   **Bug 3: Missing Tools for Most Agents**
    *   **Problem:** Only the `doctor` agent was assigned a tool, leaving the other agents unable to access or process the PDF data.
    *   **Fix:** The `blood_pdf_tool` was added to all agents that require access to the report's content, ensuring they can perform their roles.
        ```python
        # Before
        verifier = Agent(...)  # No tools
        
        # After
        verifier = Agent(..., tools=[blood_pdf_tool])
        ```

### `tools.py` - Tool System Issues

*   **Bug 1: Incorrect Class Structure**
    *   **Problem:** The PDF reader tool was defined as a simple class that did not inherit from `BaseTool`, making it incompatible with the CrewAI framework.
    *   **Fix:** The class was refactored to inherit from `BaseTool` and the primary logic was placed in the required `_run` method.
        ```python
        # Before
        class BloodTestReportTool():
            async def read_data_tool(path='data/sample.pdf'): # Not a proper tool
                ...
        
        # After
        class BloodPDFTool(BaseTool):
            name: str = "Blood Test PDF Reader"
            def _run(self, file_path: str): #  Proper CrewAI tool method
                ...
        ```

*   **Bug 2: Hardcoded File Path**
    *   **Problem:** The tool had a hardcoded default file path, causing it to ignore the user's uploaded file and analyze the same sample PDF every time.
    *   **Fix:** The hardcoded default was removed. The `_run` method now correctly uses the `file_path` parameter passed dynamically from the agent.
        ```python
        # Before
        async def read_data_tool(path='data/sample.pdf'):  # Hardcoded default
            ...
        # After
        def _run(self, file_path: str):  # Uses parameter from agent
            ...
        ```

*   **Bug 3: Missing Error Handling & Instantiation**
    *   **Problem:** The tool lacked `try...except` blocks to handle PDF parsing failures, and the class was never instantiated, so it could not be used.
    *   **Fix:** Added comprehensive error handling for file I/O and created an instance of the tool class that can be imported by other modules.
        ```python
        # After
        try:
            docs = PyPDFLoader(file_path=file_path).load()
            return full_report
        except Exception as e:
            return f"Error reading PDF file: {str(e)}"
        
        blood_pdf_tool = BloodPDFTool()
        ```

### `task.py` - Task Configuration Issues

*   **Bug 1: Wrong Agent Assignments**
    *   **Problem:** All analytical tasks were incorrectly assigned to the `doctor` agent, ignoring the specialized roles of other agents.
    *   **Fix:** Each task is now assigned to its appropriate specialist agent (e.g., `verification` to `verifier`, `nutrition_analysis` to `nutritionist`).
        ```python
        # Before
        nutrition_analysis = Task(..., agent=doctor, ...)  # Should be nutritionist
        
        # After
        nutrition_analysis = Task(..., agent=nutritionist, ...)
        ```

*   **Bug 2: Incorrect Tool References**
    *   **Problem:** Tasks were referencing a non-existent tool method (`BloodTestReportTool.read_data_tool`).
    *   **Fix:** All tasks now reference the correct, instantiated tool variable (`blood_pdf_tool`).
        ```python
        # Before
        verification = Task(..., tools=[BloodTestReportTool.read_data_tool])
        
        # After
        verification = Task(..., tools=[blood_pdf_tool])
        ```

*   **Bug 3: Incorrect Task Order**
    *   **Problem:** The `verification` task was defined last in the file, but logically it must run first to validate the input.
    *   **Fix:** The tasks were reordered to ensure a logical flow, with `verification` placed first. In the `Crew` definition, the task list also reflects this correct sequential order.

---

## Setup and Usage Instructions

### Prerequisites
Before you begin, ensure you have the following services installed and running on your local machine:
*   **Redis:** Running on the default port `6379`.
*   **MongoDB:** Running on the default port `27017`.

### Step 1: Clone the Repository
```bash
git clone https://github.com/MilindJain03/Debug-assignment.git
cd Debug-assignment
```

### Step 2: Create and Activate a Virtual Environment
```bash
# For MacOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
Create a file named `.env` in the root of the project directory. This file connects the application to your local services and AI provider.
```env
# .env file
GEMINI_API_KEY="your-google-api-key"
MONGO_URI="mongodb://localhost:27017/"
MONGO_DB_NAME="blood_analysis_db"
REDIS_URL="redis://localhost:6379/0"
```

### Step 5: Run the System
You will need to open **two separate terminals** to run the application components. Make sure to activate the virtual environment in both.

*   **Terminal 1: Start the Celery Worker**
    ```bash
    celery -A worker.celery_app worker --loglevel=info
    ```

*   **Terminal 2: Start the FastAPI Server**
    ```bash
    uvicorn main:app --reload
    ```
The API is now live and accessible at `http://127.0.0.1:8000`.

---

## API Documentation

Access the interactive Swagger UI documentation, which is automatically generated by FastAPI, at `http://127.0.0.1:8000/docs`.

### 1. Start Analysis

*   **Endpoint:** `POST /analyze`
*   **Description:** Submits a PDF blood report for asynchronous analysis.
*   **Success Response (`202 Accepted`)**
    ```json
    {
        "message": "Analysis has been started. Please check the result later.",
        "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "status_endpoint": "/result/a1b2c3d4-e5f6-7890-1234-567890abcdef"
    }
    ```

### 2. Get Analysis Result

*   **Endpoint:** `GET /result/{task_id}`
*   **Description:** Poll this endpoint with the `task_id` from the previous step to check the status and retrieve the result of the analysis.
*   **Success Response (`200 OK` - when `COMPLETED`)**
    ```json
    {
        "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "status": "COMPLETED",
        "analysis": "## Medical Analysis Summary\nYour hemoglobin is slightly low...\n\n## Nutritional Recommendations\nWe recommend increasing your intake of iron-rich foods...\n\n## Recommended Fitness Plan\n..."
    }
    ```
