import os
from dotenv import load_dotenv
from crewai import Agent
from litellm import completion
from tools import search_tool, blood_test_tool, nutrition_tool, exercise_tool
from crewai import LLM

load_dotenv()

# Initialize LLM with Gemini 1.5 Flash
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

llm = LLM(
    model="gemini/gemini-2.0-flash",
    temperature=0.7,
)


# Doctor Agent
doctor = Agent(
    role="Senior Experienced Doctor",
    goal="Provide a detailed medical analysis of blood test reports based on user queries",
    verbose=True,
    memory=True,
    backstory=(
        "You're a highly experienced doctor with a flair for diagnosing conditions. "
        "You analyze blood test reports thoroughly and provide clear, evidence-based advice. "
        "You avoid unnecessary speculation and focus on actionable recommendations."
    ),
    # The doctor's primary tool is their knowledge to analyze the text provided by the verifier.
    # A search tool is not needed for this initial analysis.
    tools=[], 
    llm=llm,
    max_iter=5,
    max_rpm=100,
    allow_delegation=False
)

# Verifier Agent
verifier = Agent(
    role="Blood Report Verifier",
    goal="Verify that the uploaded file is a valid blood test report and extract its text content",
    verbose=True,
    memory=True,
    backstory=(
        "You specialize in validating medical documents. "
        "You carefully check if an uploaded file is a blood test report before analysis. "
        "You ensure data integrity and flag invalid inputs, passing on only the raw text of valid reports."
    ),
    tools=[blood_test_tool],
    llm=llm,
    max_iter=5,
    max_rpm=100,
    allow_delegation=False
)

# Nutritionist Agent
nutritionist = Agent(
    role="Clinical Nutritionist",
    goal="Provide personalized nutrition recommendations based on a medical summary of blood test results",
    verbose=True,
    backstory=(
        "You are a certified nutritionist with 15+ years of experience. "
        "You analyze medical summaries to recommend personalized diets and supplements. "
        "You rely on scientific evidence and avoid unverified claims."
    ),
    tools=[nutrition_tool, search_tool],
    llm=llm,
    max_iter=5,
    max_rpm=100,
    allow_delegation=False
)

# Exercise Specialist Agent
exercise_specialist = Agent(
    role="Certified Fitness Coach",
    goal="Create safe and effective exercise plans based on a medical summary of blood test results",
    verbose=True,
    backstory=(
        "You are a certified fitness coach who designs tailored exercise plans. "
        "You consider health conditions and medical data to ensure safety. "
        "You promote balanced fitness routines for long-term health."
    ),
    tools=[exercise_tool, search_tool],
    llm=llm,
    max_iter=5,
    max_rpm=100,
    allow_delegation=False
)

# New Agent: Report Compiler
compiler_agent = Agent(
    role="Medical Report Compiler",
    goal="Compile individual analyses from the doctor, nutritionist, and fitness coach into a single, cohesive report",
    verbose=True,
    memory=True,
    backstory=(
        "You are a skilled medical editor. Your expertise lies in taking complex medical information from various specialists "
        "and organizing it into a clear, easy-to-read, and comprehensive report for the patient. "
        "You ensure the final document is well-structured and presentable."
    ),
    tools=[],
    llm=llm,
    allow_delegation=False
)