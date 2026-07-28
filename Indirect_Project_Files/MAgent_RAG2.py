import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, PDFSearchTool, WebsiteSearchTool
from crewai.tools import tool



##

## To run this code
## type:  python MAgent_RAG2.py below in the terminal

# Load the environment variables from .env file
## Recall this contains KEYS for OpenAI's LLM
## as well as for serper to Google search
load_dotenv()

llm = "gpt-4o-mini"

# Initialize the Serper search tool
google_search_tool = SerperDevTool()

# =====================================================================
# RAG: Initialize the pdf Search Tool
# =====================================================================
# This tool opens a raw PDF, chunks the text, and sets up a local 
# Chroma vector index automatically behind the scenes.
# Ensure a file named "my_resume_name.pdf" (whatever YOUR resume name is)
# exists in your VS Code workspace directory - in your Project Folder.
resume_rag_tool = PDFSearchTool(
    pdf="AmiGates_CV_2026_2.pdf",
    config={
        "llm": {
            "provider": "openai",
            "config": {"model": "gpt-4o-mini", "temperature": 0.1}
        },
        "embedder": {
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"}
        }
    }
)

# ========================================================
# Define the University Website Searcher tool for DS and CS
# ========================================================

ds_courses_tool = WebsiteSearchTool(
    website="https://catalog.colorado.edu/courses-a-z/dtsa/",
    config={"llm": {"provider": "openai", "config": {"model": "gpt-4o-mini"}}}
)

# Tool for the Computer Science curriculum page
cs_courses_tool = WebsiteSearchTool(
    website="https://catalog.colorado.edu/courses-a-z/csci/",
    config={"llm": {"provider": "openai", "config": {"model": "gpt-4o-mini"}}}
)

# ========================================================
# Define a Course Advisor AGent Based on Job/skill deficits
# ========================================================
CourseAdvisor = Agent(
    role="University Course Advisor",
    goal="Identify specific university courses that will bridge a candidate's technical skill gaps for data science and AI roles",
    backstory="You are an academic advisor specializing in aligning university curricula with tech industry demands. You analyze job skill gaps and search university course listings to find exact course matches.",
    verbose=True,
    llm=llm,
    allow_delegation=False,
    tools=[ds_courses_tool, cs_courses_tool],
    max_iter=5,
    max_rpm=10
)

# ========================================================
# Define the Job Hunter Agent with safety built in
# ========================================================
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

#========================================================
# Define the Writer Agent
#========================================================
JobLister = Agent(
    role="Job Options Lister",
    goal="Create useful and applicable information about job options and listing \ in the areas of data science, machine learning, and AI",
    backstory="""You are a skilled writer who transforms dense job listings and job related information into clear, useful, and applicable blog posts. You make job requirements and focusses easy for to understand and to apply for.""",
    verbose=True,
    llm = llm, 
    allow_delegation=False,
    
    # Give this agent access to the PDF RAG tool
    tools=[resume_rag_tool], 
    
    max_iter=3,
    max_rpm=10
)


#========================================================
# Define the Job Search Task
#========================================================
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



#========================================================
# Define the Course Recommendation Task
#========================================================
course_recommendation_task = Task(
    description="""1. Read ONLY the 'skill gaps' section from the 
    previous report. 
    2. Completely ignore any courses or history listed on the 
    candidate's resume.
    3. Use your ds_courses_tool, cs_courses_tool to actively query the CU 
    Boulder website catalog.
    4. Find NEW, un-taken courses that match those missing skills.
    
    CRITICAL: Do not recommend any course the candidate has already 
    taken or taught. You must pull live data from the website tool.""",
    expected_output="A list of 3 brand-new CU Boulder courses from " \
    "the website tool matching the skill gaps.",
    agent=CourseAdvisor,
    tools=[ds_courses_tool, cs_courses_tool]
)

#========================================================
# Define the Writing Task
#========================================================
job_write_task = Task(
    description="""Using the job search summary provided by JobHunter as well as course recommendations 
    from the CourseAdvisor, and using your resume_rag_tool to read the resume. ANd using ds_courses_tool, cs_courses_tool
     to determine areas where the candiate can fill in missing gaps in knowledge with respect to 
     a comparison between their resume and the jobs listed
    Cross-reference the found jobs with the skills on the resume. Write a markdown blog post that highlights these roles, 
    explains how well they match the resume stack, and notes any skill gaps.""",
    expected_output="A focused and easy to review formatted markdown blog post with a clear " \
                    "list of jobs, their key requirements, and a personalized resume alignment analysis.",
    agent=JobLister,
    output_file="ai_agents_job_report41.md"
)

#========================================================
# Assemble the Crew
#========================================================
job_crew = Crew(
    agents=[JobHunter, JobLister, CourseAdvisor],
    tasks=[job_search_task, course_recommendation_task, job_write_task],
    process=Process.sequential, 
    verbose=True 
)

if __name__ == "__main__":
    print("\n## Starting the Multi-Agent Workflow via setup.ps1...")
    result = job_crew.kickoff()
    print("\n## Workflow Completed Successfully! Check ai_agents_job_report41.md")
    print(result.raw) 