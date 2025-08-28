# Fix SQLite compatibility issue for ChromaDB
import os
os.environ["ALLOW_RESET"] = "TRUE"

from crew import BrellaResearchCrew
import json, csv, argparse
import os
from dotenv import load_dotenv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tools.google_sheets_exporter import GoogleSheetsExporter

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

if not os.getenv("SERPER_API_KEY"):
    print("Warning: SERPER_API_KEY not found in environment variables")

# Check for Brella authentication credentials
if os.getenv("BRELLA_EMAIL") and os.getenv("BRELLA_PASSWORD"):
    print("Brella authentication credentials found - authenticated scraping enabled")
else:
    print("Note: Set BRELLA_EMAIL and BRELLA_PASSWORD in .env for authenticated portal access")

sheets_exporter = None
if os.getenv("GOOGLE_SPREADSHEET_URL"):
    sheets_exporter = GoogleSheetsExporter(spreadsheet_url=os.getenv("GOOGLE_SPREADSHEET_URL"))
    print(f"Using Google Spreadsheet URL: {os.getenv('GOOGLE_SPREADSHEET_URL')}")
elif os.getenv("GOOGLE_CREDENTIALS_PATH"):
    if os.path.exists(os.getenv("GOOGLE_CREDENTIALS_PATH")):
        sheets_exporter = GoogleSheetsExporter(credentials_file=os.getenv("GOOGLE_CREDENTIALS_PATH"))
    else:
        print(f"Warning: Google credentials file not found at {os.getenv('GOOGLE_CREDENTIALS_PATH')}")
        print("Results will not be exported to Google Sheets")
else:
    print("Note: Neither GOOGLE_SPREADSHEET_URL nor GOOGLE_CREDENTIALS_PATH set in environment variables")
    print("To export to Google Sheets, use --spreadsheet-url parameter")

def research_brella(search_term, category="all", attendee_type="founders"):
    """
    Research information on Brella.io based on search term and category
    """
    print(f"Researching '{search_term}' in category '{category}' on Brella.io...")
    
    try:
        crew_instance = BrellaResearchCrew()
        crew = crew_instance.crew()
        
        search_with_category = f"{search_term} (category: {category})"
        
        result = crew.kickoff(inputs={
            "search_term": search_with_category,
            "attendee_type": attendee_type
        })
        
        output = {
            "search_term": search_term,
            "category": category,
            "attendee_type": attendee_type,
            "events": crew_instance.event_task.output.raw if hasattr(crew_instance.event_task, 'output') else "Not available",
            "companies": crew_instance.company_task.output.raw if hasattr(crew_instance.company_task, 'output') else "Not available",
            "networking": crew_instance.networking_task.output.raw if hasattr(crew_instance.networking_task, 'output') else "Not available",
            "founders": crew_instance.founder_task.output.raw if hasattr(crew_instance.founder_task, 'output') else "Not available",
            "attendees": crew_instance.attendee_task.output.raw if hasattr(crew_instance.attendee_task, 'output') else "Not available",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return output
    except Exception as e:
        print(f"Error researching '{search_term}' on Brella.io: {str(e)}")
        return {
            "search_term": search_term,
            "category": category,
            "attendee_type": attendee_type,
            "events": f"Error: {str(e)}",
            "companies": f"Error: {str(e)}",
            "networking": f"Error: {str(e)}",
            "founders": f"Error: {str(e)}",
            "attendees": f"Error: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def process_csv(csv_file, output_file, max_workers=3):
    """
    Process a CSV file with search terms and categories
    """
    search_items = []
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  
        
        term_idx = header.index('Search Term') if 'Search Term' in header else 0
        category_idx = header.index('Category') if 'Category' in header else 1
        attendee_idx = header.index('Attendee Type') if 'Attendee Type' in header else 2
        
        for row in reader:
            if len(row) > term_idx:
                category = row[category_idx] if len(row) > category_idx else "all"
                attendee_type = row[attendee_idx] if len(row) > attendee_idx else "founders"
                search_items.append((row[term_idx], category, attendee_type))
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_search = {
            executor.submit(research_brella, term, category, attendee_type): (term, category, attendee_type) 
            for term, category, attendee_type in search_items
        }
        
        for future in as_completed(future_to_search):
            term, category, attendee_type = future_to_search[future]
            try:
                result = future.result()
                results.append(result)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                
                print(f"Completed research for '{term}' in category '{category}' for {attendee_type}")
            except Exception as e:
                print(f"Error processing '{term}' in category '{category}' for {attendee_type}: {str(e)}")
    
    return results

def main():
    global sheets_exporter
    
    parser = argparse.ArgumentParser(description='Research information on Brella.io')
    
    # Create a mutually exclusive group for input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--csv', type=str, help='CSV file with search terms and categories')
    input_group.add_argument('--term', type=str, help='Search term')
    
    parser.add_argument('--category', type=str, default='all', 
                        choices=['all', 'events', 'companies', 'people', 'networking', 'founders'],
                        help='Category to search in (default: all)')
    parser.add_argument('--attendee-type', type=str, default='founders',
                        choices=['founders', 'investors', 'executives', 'speakers', 'attendees', 'all'],
                        help='Type of people to find at events (default: founders)')
    parser.add_argument('--output', type=str, default='brella_results.json', help='Output JSON file')
    parser.add_argument('--workers', type=int, default=3, help='Maximum number of parallel workers')
    parser.add_argument('--sheets', action='store_true', help='Export results to Google Sheets')
    parser.add_argument('--spreadsheet', type=str, default='Brella Research Results', help='Google Spreadsheet name (when not using URL)')
    parser.add_argument('--spreadsheet-url', type=str, help='Direct URL to a Google Spreadsheet')
    parser.add_argument('--worksheet', type=str, help='Google Worksheet name (defaults to current date)')
    
    args = parser.parse_args()
    
    if args.csv:
        results = process_csv(args.csv, args.output, args.workers)
    else: 
        result = research_brella(args.term, args.category, getattr(args, 'attendee_type', 'founders'))
        results = [result]
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    
    print(f"Research completed. Results saved to {args.output}")
    
    should_export_to_sheets = args.sheets or (sheets_exporter is not None and os.getenv("GOOGLE_SPREADSHEET_URL"))
    
    if should_export_to_sheets:
        if args.spreadsheet_url:
            if not sheets_exporter:
                sheets_exporter = GoogleSheetsExporter(spreadsheet_url=args.spreadsheet_url)
            else:
                sheets_exporter.spreadsheet_url = args.spreadsheet_url
                sheets_exporter.spreadsheet_id = sheets_exporter._extract_spreadsheet_id(args.spreadsheet_url)
            
            print(f"Exporting results to Google Sheets at URL: {args.spreadsheet_url}")
        elif sheets_exporter:
            print(f"Exporting results to Google Sheets using URL from .env file")
        else:
            print("Error: No Google Sheets URL or credentials provided.")
            print("Use --spreadsheet-url parameter or set GOOGLE_SPREADSHEET_URL in .env file")
            print("Results will not be exported to Google Sheets")
            
        if sheets_exporter:
            if sheets_exporter.authenticate():
                spreadsheet_url = sheets_exporter.export_to_sheet(
                    results, 
                    args.spreadsheet, 
                    args.worksheet
                )
                
                if spreadsheet_url:
                    print(f"Results exported successfully to Google Sheets: {spreadsheet_url}")
                else:
                    print("Failed to export results to Google Sheets")
            else:
                print("Failed to authenticate with Google Sheets API")
    
    print("\nSummary:")
    for result in results:
        attendee_type = result.get('attendee_type', 'founders')
        print(f"- '{result['search_term']}' in '{result['category']}' ({attendee_type}): " +
              f"Events: {'Found' if result['events'] != 'Not available' else 'Not found'}, " +
              f"Companies: {'Found' if result['companies'] != 'Not available' else 'Not found'}, " +
              f"Networking: {'Found' if result['networking'] != 'Not available' else 'Not found'}, " +
              f"Founders: {'Found' if result['founders'] != 'Not available' else 'Not found'}, " +
              f"Attendees: {'Found' if result.get('attendees', 'Not available') != 'Not available' else 'Not found'}")

if __name__ == "__main__":
    main()