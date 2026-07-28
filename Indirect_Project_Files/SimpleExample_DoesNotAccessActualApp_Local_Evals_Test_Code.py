import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field

# Load your local environment variables (OpenAI API Key)
load_dotenv()

# Verify the API key is present
if not os.environ.get("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY is missing from your environment variables!")

# 1. Define the Pydantic structure for the Judge's output
class EvaluationReport(BaseModel):
    score: int = Field(description="A score from 1 to 5 based strictly on the rubric criteria.")
    reasoning: str = Field(description="Detailed academic justification for the assigned score.")

# 2. Your exact evaluation crew function
def run_evaluation_crew(resume_text, generated_report):
    judge_llm = LLM(model="openai/gpt-4o-mini", temperature=0.0)

    evaluator_agent = Agent(
        role="Senior Academic Evaluator",
        goal="Audit career advisory reports to ensure they are 100% faithful to the source resume.",
        backstory="""You are an expert auditor. Your job is to catch AI hallucinations. You have zero 
        tolerance for career reports that suggest courses the student has already completed or taught.""",
        llm=judge_llm,
        verbose=True # Set to True locally so you can see the judge thinking in the terminal
    )

    evaluation_task = Task(
        description=f"""Analyze the following candidate resume and the corresponding generated career report.
        
        Candidate Resume:
        {resume_text}
        
        Generated Career Report:
        {generated_report}
        
        CRITICAL RUBRIC CRITERIA:
        - 5 (Excellent): All course recommendations are entirely new and justified based on missing gaps.
        - 3 (Moderate): The courses are relevant, but the alignment reasoning is vague.
        - 1 (Fail): The report recommended a course that the student has ALREADY taken or taught on their resume.
        """,
        expected_output="A structured evaluation report containing a 1-5 score and comprehensive reasoning.",
        agent=evaluator_agent,
        output_pydantic=EvaluationReport
    )

    eval_crew = Crew(
        agents=[evaluator_agent],
        tasks=[evaluation_task],
        process=Process.sequential
    )

    try:
        result = eval_crew.kickoff()
        return {
            "score": result.pydantic.score,
            "reasoning": result.pydantic.reasoning
        }
    except Exception as e:
        return {"score": 0, "reasoning": f"CrewAI Mini-Judge failed: {str(e)}"}

# 3. Execution block with a "Hallucination Trap" to test the Judge
if __name__ == "__main__":
    print("Starting Local Evaluation Test...")
    
    # Mock data where the agent failed (It recommended Python, which is already on the resume)
    mock_resume = "Experience: 3 years as a Backend Dev. Skills: Python, Django, SQL. Completed: Intro to Python."
    mock_hallucinated_report = "Based on our analysis, we highly recommend you enroll in 'Intro to Python' to fix your gaps."

    print("\n--- Running Judge against a 'FAIL' scenario (Should score 1) ---")
    results = run_evaluation_crew(mock_resume, mock_hallucinated_report)
    
    print("\n --- FINAL JUDGE RESULTS ---")
    print(f"Score: {results['score']} / 5")
    print(f"Reasoning: {results['reasoning']}")
