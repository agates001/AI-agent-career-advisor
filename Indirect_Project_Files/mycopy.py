import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# Load the environment variables from .env file
## Recall this contains KEYS for OpenAI's LLM
## as well as for serper to Google search
load_dotenv()

# Initialize the Serper search tool
google_search_tool = SerperDevTool()

# Define the Researcher Agent with safety guardrails
researcher = Agent(
    role="Senior Research Analyst",
    role_description="Investigate cutting-edge tech trends.", # [INDUSTRY STANDARD] Enterprise code explicitly defines role descriptions to enforce strict alignment across dozens of agents.
    goal="Uncover cutting-edge developments in multi-agent AI systems",
    backstory="""You are an expert research analyst. You excel at sifting through 
    online data, academic papers, and news to find the most accurate and 
    forward-looking information.""",
    verbose=True,
    allow_delegation=False,
    tools=[google_search_tool],
    
    # Cost & Safety Settings for Students:
    max_iter=5,      
    # [INDUSTRY STANDARD] max_iter=15 to 25 -> Production agents are given more "thinking room" to retry failed web queries, but this increases API token costs.
    
    max_rpm=10       
    # [INDUSTRY STANDARD] max_rpm=None -> Enterprise accounts use high-tier API plans with custom rate limits, so they do not artificially throttle agent speed.
)

# Define the Writer Agent with safety guardrails
writer = Agent(
    role="Tech Content Writer",
    role_description="Draft clear, educational tech content.", # [INDUSTRY STANDARD] Added for architectural consistency in professional environments.
    goal="Create engaging, accessible articles about complex tech topics",
    backstory="""You are a skilled writer who transforms dense technical research 
    into clear, compelling, and educational blog posts. You make complex topics 
    easy for graduate students to understand.""",
    verbose=True,
    allow_delegation=False,
    
    # Cost & Safety Settings for Students:
    max_iter=3,      
    # [INDUSTRY STANDARD] max_iter=10 -> Writers rarely loop, but production code allows higher limits to handle complex data synthesis without cutting off.
    
    max_rpm=10       
    # [INDUSTRY STANDARD] max_rpm=None -> Throttling is removed in enterprise setups to ensure the fastest possible execution time.
)

# Define the Research Task
research_task = Task(
    description="""Investigate the latest trends in multi-agent AI systems for 2026. 
    Focus on practical use cases in education and research. Identify 3 key breakthroughs.""",
    expected_output="A bulleted summary of 3 major AI agent breakthroughs with source context.",
    agent=researcher,
    tools=[search_tool]
)

# Define the Writing Task
write_task = Task(
    description="""Using the research summary provided, write a 300-word educational 
    blog post suitable for university students. Focus on why these breakthroughs matter.""",
    expected_output="A beautifully formatted markdown blog post with a catchy title.",
    agent=writer,
    output_file="ai_agents_report.md"
)

# Assemble the Crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True
    # [INDUSTRY STANDARD] memory=True -> Enterprise crews often use an underlying vector database (like ChromaDB) to remember past execution details, which increases setup complexity and infrastructure cost.
)

if __name__ == "__main__":
    print("\n## Starting the Multi-Agent Workflow via setup.ps1...")
    result = crew.kickoff()
    print("\n## Workflow Completed Successfully! Check ai_agents_report.md")