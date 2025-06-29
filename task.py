from crewai import Task
from agents import verifier, doctor, nutritionist, exercise_specialist, compiler_agent

# Task for Verifier Agent: To verify the document and extract text
verification = Task(
    description=(
        "1. Receive the file path: '{file_path}'.\n"
        "2. Use the 'Blood Test Report Reading Tool' to extract text from the PDF at the given path.\n"
        "3. Analyze the extracted text to determine if it is a blood test report. Look for keywords like 'Blood Test', 'Hematology', 'Cholesterol', patient details, and tables with test results.\n"
        "4. If the text extraction fails or the content is not a blood report, your final answer must state that it's an invalid file and explain why.\n"
        "5. If it is a valid report, your final answer must be ONLY the full extracted text from the report. Do not add any other words, greetings, or explanations."
    ),
    expected_output=(
        "The full, raw text extracted from the blood test report PDF, or an error message stating the file is not a valid blood test report."
    ),
    agent=verifier,
)

# Task for Doctor Agent: To analyze the report
help_patients = Task(
    description=(
        "Analyze the provided blood test report text to create a comprehensive medical summary. The user's specific query is: '{query}'.\n"
        "Your analysis should:\n"
        "- Summarize the key findings from the report.\n"
        "- Identify all values that are outside the normal reference ranges.\n"
        "- For each abnormal value, explain its potential health implications in simple terms.\n"
        "- Address the user's specific query directly.\n"
        "- Conclude with general, actionable advice. Do not provide a definitive diagnosis or prescribe medication."
    ),
    expected_output=(
        "A detailed, easy-to-understand medical summary of the blood report. This output must be in two parts:\n"
        "1. A human-readable analysis for the patient.\n"
        "2. A concise, structured summary of key abnormal findings and health notes, clearly marked for the 'Nutritionist' and 'Fitness Coach' to use."
    ),
    agent=doctor,
    context=[verification],
)

# Task for Nutritionist Agent
nutrition_analysis = Task(
    description=(
        "Using the structured summary from the doctor's analysis, create a personalized nutrition plan. "
        "Focus on the key abnormal findings highlighted by the doctor. "
        "Use the 'Nutrition Recommendation Tool' to generate a detailed plan. "
        "If you need more information about a specific food or nutrient, use the search tool."
    ),
    expected_output=(
        "A detailed nutrition plan tailored to the patient's blood test results. The plan should be well-structured with sections for dietary goals, recommended foods, foods to avoid, and a sample meal plan."
    ),
    agent=nutritionist,
    context=[help_patients],
)

# Task for Exercise Specialist Agent
exercise_planning = Task(
    description=(
        "Using the structured summary from the doctor's analysis, create a personalized and safe exercise plan. "
        "Pay close attention to any health notes or precautions mentioned by the doctor (e.g., bone health, potential fatigue). "
        "Use the 'Exercise Plan Tool' to generate the plan. "
        "If you need to research safe exercises for specific conditions, use the search tool."
    ),
    expected_output=(
        "A structured weekly exercise plan suitable for the patient's health profile. It should include fitness goals, a weekly schedule, and details on cardio, strength, and flexibility exercises, along with a clear 'Precautions' section."
    ),
    agent=exercise_specialist,
    context=[help_patients],
)

# New Task: Compile the final report
compile_report_task = Task(
    description=(
        "Compile the analyses from the Doctor, Nutritionist, and Fitness Coach into a single, cohesive report. "
        "The final output should be a well-structured markdown document presented to the end-user.\n"
        "Structure the report with the following sections:\n"
        "- ## Medical Analysis Summary (from the Doctor)\n"
        "- ## Nutritional Recommendations (from the Nutritionist)\n"
        "- ## Recommended Fitness Plan (from the Fitness Coach)\n"
        "- ### Important Disclaimer\n"
        "Ensure the final report is easy to read, professional, and empathetic in tone. If any section is incomplete or contains an error message, include that information gracefully in the report."
    ),
    expected_output=(
        "A complete, well-formatted markdown report combining all the specialist analyses. "
        "This report is the final output of the entire process."
    ),
    agent=compiler_agent,
    context=[help_patients, nutrition_analysis, exercise_planning],
)