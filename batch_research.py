from crew import CompanyResearchCrew
import json, sys, argparse
import os
from dotenv import load_dotenv
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv()

# Check if API keys are loaded
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

if not os.getenv("SERPER_API_KEY"):
    print("Warning: SERPER_API_KEY not found in environment variables")

def research_company(founder_name, company_name):
    """
    Research a single company and its founder
    """
    print(f"Researching {founder_name} of {company_name}...")
    
    try:
        crew_instance = CompanyResearchCrew()
        crew = crew_instance.crew()
        
        # Pass inputs to the kickoff method
        result = crew.kickoff(inputs={
            "founder_name": founder_name,
            "company_name": company_name
        })
        
        # Extract the raw output from each task
        output = {
            "founder_name": founder_name,
            "company_name": company_name,
            "linkedin": crew_instance.linkedin_task.output.raw if hasattr(crew_instance.linkedin_task, 'output') else "Not available",
            "about": crew_instance.company_info_task.output.raw if hasattr(crew_instance.company_info_task, 'output') else "Not available",
            "website": crew_instance.website_task.output.raw if hasattr(crew_instance.website_task, 'output') else "Not available",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return output
    except Exception as e:
        print(f"Error researching {founder_name} of {company_name}: {str(e)}")
        return {
            "founder_name": founder_name,
            "company_name": company_name,
            "linkedin": f"Error: {str(e)}",
            "about": f"Error: {str(e)}",
            "website": f"Error: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def process_json_list(json_file, output_file, max_workers=3, start_index=0, end_index=None):
    """
    Process a JSON file with founder and company information
    """
    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Slice the data if needed
    if end_index is None:
        end_index = len(data)
    
    data_to_process = data[start_index:end_index]
    
    # Extract founder and company information
    founders_companies = []
    for item in data_to_process:
        if "name" in item and "company" in item:
            founders_companies.append((item["name"], item["company"]))
    
    results = []
    
    # Load existing results if the output file exists
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            print(f"Loaded {len(results)} existing results from {output_file}")
        except Exception as e:
            print(f"Error loading existing results: {str(e)}")
    
    # Create a set of already processed founders and companies
    processed = {(r["founder_name"], r["company_name"]) for r in results}
    
    # Filter out already processed items
    to_process = [(f, c) for f, c in founders_companies if (f, c) not in processed]
    
    print(f"Found {len(founders_companies)} entries in the JSON file")
    print(f"Already processed {len(processed)} entries")
    print(f"Will process {len(to_process)} new entries")
    
    # Process in parallel with a limited number of workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_founder = {
            executor.submit(research_company, founder, company): (founder, company) 
            for founder, company in to_process
        }
        
        for future in as_completed(future_to_founder):
            founder, company = future_to_founder[future]
            try:
                result = future.result()
                results.append(result)
                
                # Save intermediate results to avoid losing data if the process is interrupted
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                
                print(f"Completed research for {founder} of {company}")
            except Exception as e:
                print(f"Error processing {founder} of {company}: {str(e)}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Research companies and their founders from a JSON list')
    
    parser.add_argument('--input', type=str, default='list.json', help='Input JSON file with founder and company information')
    parser.add_argument('--output', type=str, default='research_results.json', help='Output JSON file')
    parser.add_argument('--workers', type=int, default=3, help='Maximum number of parallel workers')
    parser.add_argument('--start', type=int, default=0, help='Start index in the JSON list')
    parser.add_argument('--end', type=int, default=None, help='End index in the JSON list')
    
    args = parser.parse_args()
    
    # Process the JSON list
    results = process_json_list(args.input, args.output, args.workers, args.start, args.end)
    
    print(f"Research completed. Results saved to {args.output}")
    
    # Print a summary of the results
    print("\nSummary:")
    for result in results:
        print(f"- {result['founder_name']} of {result['company_name']}: LinkedIn: {'Found' if result['linkedin'] != 'Not available' else 'Not found'}, Website: {'Found' if result['website'] != 'Not available' else 'Not found'}")

if __name__ == "__main__":
    main()