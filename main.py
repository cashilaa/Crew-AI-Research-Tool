from crew import CompanyResearchCrew
import json, sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if API keys are loaded
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

if not os.getenv("SERPER_API_KEY"):
    print("Warning: SERPER_API_KEY not found in environment variables")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <founder_name> <company_name>")
        sys.exit(1)
        
    founder, company = sys.argv[1:3]
    crew_instance = CompanyResearchCrew()
    crew = crew_instance.crew()
    
    # Pass inputs to the kickoff method
    result = crew.kickoff(inputs={
        "founder_name": founder,
        "company_name": company
    })
    
    # Extract the raw output from each task
    output = {
        "linkedin": crew_instance.linkedin_task.output.raw if hasattr(crew_instance.linkedin_task, 'output') else "Not available",
        "about": crew_instance.company_info_task.output.raw if hasattr(crew_instance.company_info_task, 'output') else "Not available",
        "website": crew_instance.website_task.output.raw if hasattr(crew_instance.website_task, 'output') else "Not available"
    }
    
    print(json.dumps(output, indent=2))
