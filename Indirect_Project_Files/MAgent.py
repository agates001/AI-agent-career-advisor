import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, PDFSearchTool 
from crewai.tools import tool



## To run this code
## type:  python MAgent.py below in the terminal

# Load the environment variables from .env file
## Recall this contains KEYS for OpenAI's LLM
## as well as for serper to Google search
load_dotenv()

llm = "gpt-4o-mini"

# Initialize the Serper search tool
google_search_tool = SerperDevTool()

# Define the Job Hunter Agent with safety built in
JobHunter = Agent(
    role="DS Job Hunter",
    goal="Find current and open jobs in the area of data science, machine learning, and AI",
    backstory="""You are job hunter. You search through 
    online job data, specifically in the areas of data science, machine learning, and AI, to find 
    open jobs.""",
    verbose=True,
    llm = llm,
    allow_delegation=False,
    tools=[google_search_tool],   
    # Cost & Safety Settings 
    max_iter=5,      
    # NOTICE: max_iter=15 to 25 -> Normally Production agents are given 
    # more "thinking room" to retry failed web queries, but this increases API token costs. 
    max_rpm=10       
    # NOTICE: max_rpm=None -> Normally, accounts use high-tier API plans with 
    # custom rate limits, so they do not artificially throttle agent speed.
)

# Define the Writer Agent
JobLister = Agent(
    role="Job Options Lister", 
    goal="Create useful and applicable information about job options and listing \
    in the areas of data science, machine learning, and AI",
    backstory="""You are a skilled writer who transforms dense job listings and job related information 
    into clear, useful, and applicable blog posts. You make job requirements and focusses
    easy for to understand and to apply for.""",
    verbose=True,
    llm = llm, 
    # passing the model identifier directly as a string 
    # to the agent completely eliminates library schema 
    # dependency conflicts. So use llm=llm where llm is 
    # defined above.
    allow_delegation=False,
    max_iter=3,      
    max_rpm=10       
)

# Define the Job Search Task
job_search_task = Task(
    description="""Investigate the latest job listings in the areas of data science, 
    machine learning, and AI for the last month. 
    Focus on job openings that are seeking a recent graduate in the areas of data science,
    machine learning, or AI.""",
    expected_output="A bulleted summary of at least 5 " \
    "job openings with source context and for each at least 4 skills required for that job.",
    agent=JobHunter,
    tools=[google_search_tool]
)

# Define the Writing Task
job_write_task = Task(
    description="""Using the job search summary provided, write a bullet list that describes 
     the focus of the job, and at least 5 skills required.""",
    expected_output="A focused and easy to review formatted markdown blog post with a clear " \
    "list of jobs and their key topics or requirements.",
    agent=JobLister,
    output_file="ai_agents_job_report2.md"
)

# Assemble the Crew
job_crew = Crew(
    agents=[JobHunter, JobLister],
    tasks=[job_search_task, job_write_task],
    process=Process.sequential,
    # The above parameter guarantees data flows linearly. 
    # Task B (job_write_task) receives the collected context 
    # from Task A (job_search_task) automatically.
    verbose=True
    # NOTICE: memory=True -> Enterprise crews often use an underlying vector database (like ChromaDB)
    # to remember past execution details, which increases setup complexity 
    # and infrastructure cost. We will look at this and RAG later.
)

if __name__ == "__main__":
    print("\n## Starting the Multi-Agent Workflow via setup.ps1...")
    result = job_crew.kickoff()
    print("\n## Workflow Completed Successfully! Check ai_agents_job_report.md")
    print(result.raw) 