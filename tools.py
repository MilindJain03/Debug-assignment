import os
import logging
import time
import pdfplumber
from dotenv import load_dotenv
from litellm import completion
from crewai_tools import SerperDevTool
from crewai.tools.base_tool import BaseTool
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Search Tool
search_tool = SerperDevTool()

# --- Helper function for robust LLM calls with retries ---
def llm_completion_with_retry(model, messages, api_key, max_retries=2, delay=5):
    """
    Calls the LLM with retry logic for handling transient errors like rate limiting.
    """
    for attempt in range(max_retries):
        try:
            response = completion(
                model=model,
                messages=messages,
                api_key=api_key
            )
            # Check if the response is valid and has content
            if response and response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                logger.warning(f"LLM call attempt {attempt + 1} returned an empty response. Retrying in {delay} seconds...")
                time.sleep(delay)
        except Exception as e:
            logger.error(f"An exception occurred on LLM call attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return f"An error occurred after multiple retries: {e}"
    return "LLM call failed after multiple retries, returning an empty response."


# Blood Test Report Tool
class BloodTestReportTool(BaseTool):
    name: str = "Blood Test Report Reading Tool"
    description: str = "Reads and extracts all text content from a blood test report PDF. The input must be a valid file path to the PDF."

    def _run(self, file_path: str) -> str:
        try:
            logger.info(f"Processing file: {file_path}")
            if not os.path.exists(file_path):
                return f"Error: File not found at path {file_path}. Please ensure the correct path is provided."

            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if not text.strip():
                return "Error: No text could be extracted from the PDF. The file might be empty, corrupted, or contain only images."

            logger.info(f"Successfully extracted text from {file_path}.")
            return text
        except Exception as e:
            logger.error(f"Error in BloodTestReportTool while processing {file_path}: {e}", exc_info=True)
            return f"Error reading or processing the PDF file: {e}. The file might be encrypted or malformed."

# Nutrition Tool
class NutritionTool(BaseTool):
    name: str = "Nutrition Recommendation Tool"
    description: str = "Analyzes a medical summary and provides structured nutrition recommendations."

    def _run(self, blood_report_data: str) -> str:
        logger.info("Generating nutrition recommendations...")
        prompt = (
            f"You are a clinical nutritionist. Based on the following medical summary, provide personalized nutrition recommendations. "
            f"Structure your response clearly with sections for 'Dietary Changes', 'Foods to Include', 'Foods to Avoid', and 'Supplement Suggestions'. "
            f"Focus on any abnormal values mentioned. Here is the summary:\n\n{blood_report_data}"
        )
        messages = [{"role": "user", "content": prompt}]
        return llm_completion_with_retry(
            model="gemini/gemini-1.5-flash",
            messages=messages,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

# Exercise Tool
class ExerciseTool(BaseTool):
    name: str = "Exercise Plan Tool"
    description: str = "Creates a safe and effective exercise plan based on a medical summary."

    def _run(self, blood_report_data: str) -> str:
        logger.info("Generating exercise plan...")
        prompt = (
            f"You are a certified fitness coach. Based on the following medical summary, create a safe weekly exercise plan. "
            f"Tailor the plan to the user's health status. "
            f"Structure the response with sections for 'Cardiovascular Exercise', 'Strength Training', and 'Flexibility/Mobility'. "
            f"Include frequency, duration, intensity, and specific examples. Add a 'Precautions' section. "
            f"Here is the summary:\n\n{blood_report_data}"
        )
        messages = [{"role": "user", "content": prompt}]
        return llm_completion_with_retry(
            model="gemini/gemini-1.5-flash",
            messages=messages,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

# Instantiate tools
blood_test_tool = BloodTestReportTool()
nutrition_tool = NutritionTool()
exercise_tool = ExerciseTool()