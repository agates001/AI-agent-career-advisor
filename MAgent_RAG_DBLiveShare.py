import os
import streamlit as st
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, PDFSearchTool, WebsiteSearchTool
from crewai.tools import tool
from datetime import datetime, timezone
from supabase import create_client, Client
from pypdf import PdfReader

# ========================================================
# Streamlit Web User Interface Setup
# ========================================================
st.set_page_config(page_title="AI Agent Career Advisor", page_icon="🎯", layout="centered")
st.title("Multi-Agent Job & Course Advisor")
st.write("This application runs a live multi-agent workflow to search for jobs, scan your resume, and recommend matching CU Boulder courses.")

# Load the environment variables
load_dotenv()

llm = "gpt-4o-mini"

# ========================================================
# Main Execution Trigger Button
# ========================================================
if st.button("🚀 Run AI Agent Analysis"):
    st.info("Agents kicked off! They are hunting jobs, reading your resume, and scraping the CU Boulder catalog. Please wait 1-2 minutes...")
    
    with st.spinner("Agents are analyzing data..."):
        
        # Initialize the Serper search tool
        google_search_tool = SerperDevTool()

        # RAG: Initialize the pdf Search Tool
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

        # Define the University Website Searcher tools for DS and CS
        ds_courses_tool = WebsiteSearchTool(
            website="https://colorado.edu",
            config={"llm": {"provider": "openai", "config": {"model": "gpt-4o-mini"}}}
        )

        cs_courses_tool = WebsiteSearchTool(
            website="https://colorado.edu",
            config={"llm": {"provider": "openai", "config": {"model": "gpt-4o-mini"}}}
        )

        # ========================================================
        # Define Agents
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
            max_reshape=10
        )

        JobHunter = Agent(
            role="DS Job Hunter",
            goal="Find current and open jobs in the area of data science, machine learning, and AI",
            backstory="You are job hunter. You search through online job data, specifically in the areas of data science, machine learning, and AI, to find open jobs.",
            verbose=True,
            llm=llm,
            allow_delegation=False,
            tools=[google_search_tool],   
            max_iter=5,      
            max_rpm=10       
        )

        JobLister = Agent(
            role="Job Options Lister",
            goal="Create useful and applicable information about job options and listing in the areas of data science, machine learning, and AI",
            backstory="You are a skilled writer who transforms dense job listings and job related information into clear, useful, and applicable blog posts. You make job requirements and focusses easy for to understand and to apply for.",
            verbose=True,
            llm=llm, 
            allow_delegation=False,
            tools=[resume_rag_tool], 
            max_iter=3,
            max_rpm=10
        )

        # ========================================================
        # Define Tasks
        # ========================================================
        job_search_task = Task(
            description="""Investigate the latest job listings in the areas of data science, 
            machine learning, and AI for the last month. 
            Focus on job openings that are seeking a recent graduate in the areas of data science,
            machine learning, or AI.""",
            expected_output="A bulleted summary of at least 5 job openings with source context and for each at least 4 skills required for that job.",
            agent=JobHunter,
            tools=[google_search_tool]
        )

        course_recommendation_task = Task(
            description="""1. Read ONLY the 'skill gaps' section from the previous report. 
            2. Completely ignore any courses or history listed on the candidate's resume.
            3. Use your ds_courses_tool, cs_courses_tool to actively query the CU Boulder website catalog.
            4. Find NEW, un-taken courses that match those missing skills.
            CRITICAL: Do not recommend any course the candidate has already taken or taught. You must pull live data from the website tool.""",
            expected_output="A list of 3 brand-new CU Boulder courses from the website tool matching the skill gaps.",
            agent=CourseAdvisor,
            tools=[ds_courses_tool, cs_courses_tool]
        )

        job_write_task = Task(
            description="""Using the job search summary provided by JobHunter as well as course recommendations 
            from the CourseAdvisor, and using your resume_rag_tool to read the resume. ANd using ds_courses_tool, cs_courses_tool
            to determine areas where the candiate can fill in missing gaps in knowledge with respect to 
            a comparison between their resume and the jobs listed
            Cross-reference the found jobs with the skills on the resume. Write a markdown blog post that highlights these roles, 
            explains how well they match the resume stack, and notes any skill gaps.""",
            expected_output="A focused and easy to review formatted markdown blog post with a clear list of jobs, their key requirements, and a personalized resume alignment analysis.",
            agent=JobLister,
            output_file="ai_agents_job_report41.md"
        )

        # ========================================================
        # Assemble and Kickoff the Crew
        # ========================================================
        job_crew = Crew(
            agents=[JobHunter, JobLister, CourseAdvisor],
            tasks=[job_search_task, course_recommendation_task, job_write_task],
            process=Process.sequential, 
            verbose=True 
        )

        result = job_crew.kickoff()
        
        # Display the results directly inside the webpage dynamically
        st.success("Workflow Completed Successfully!")
        st.markdown("### Final Career Alignment Report")
        st.markdown(result.raw)

        # ========================================================
        # --- STREAM TO SUPABASE CLOUD  ---
        # ========================================================
        try:
            url: str = os.environ.get("SUPABASE_URL")
            key: str = os.environ.get("SUPABASE_SECRET_KEY")
            
            if url and key:
                supabase: Client = create_client(url, key)
                
                with st.spinner("📡 Syncing agent report and resume to Supabase cloud..."):
                    # Modern timezone-aware UTC timestamp fetching
                    now_utc = datetime.now(timezone.utc)
                    report_id = f"report_{int(now_utc.timestamp())}"
                    
                    # A. Extract the text content from the resume PDF
                    resume_text_content = ""
                    target_resume_path = "AmiGates_CV_2026_2.pdf"
                    
                    if os.path.exists(target_resume_path):
                        reader = PdfReader(target_resume_path)
                        for page in reader.pages:
                            resume_text_content += page.extract_text()
                    
                    # B. Push all elements directly into your cloud data row
                    supabase.table("agent_reports").upsert({  
                        "id": report_id,
                        "agent_name": "RAG_Multi_Agent",
                        "content": result.raw,  
                        "updated_at": now_utc.isoformat(),
                        "resume_text": resume_text_content  
                    }).execute()
                    
                st.success("✅ Multi-agent report and resume text successfully backed up to cloud database!")
            else:
                st.warning("⚠️ Supabase credentials missing from environment. Skipping cloud sync.")
        except Exception as e:
            st.error(f"❌ Failed to stream report to cloud: {e}")
