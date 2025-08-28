import requests
import json
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def scrape_brella_authenticated(query: str) -> str:
    """
    Simple authenticated scraper for Brella portal
    """
    try:
        session = requests.Session()
        base_url = "https://next.brella.io"
        
        # Get credentials
        email = os.getenv("BRELLA_EMAIL")
        password = os.getenv("BRELLA_PASSWORD")
        
        if not email or not password:
            return "Authentication credentials not found in environment variables"
        
        # Attempt login
        login_url = f"{base_url}/login"
        login_data = {
            'email': email,
            'password': password
        }
        
        response = session.post(login_url, data=login_data)
        
        if response.status_code == 200:
            # Try to access events
            events_url = f"{base_url}/dashboard"
            events_response = session.get(events_url)
            
            if events_response.status_code == 200:
                soup = BeautifulSoup(events_response.content, 'html.parser')
                
                # Look for event-related content
                events_found = []
                
                # Search for the query term in the page content
                if query.lower() in events_response.text.lower():
                    events_found.append({
                        "message": f"Found references to '{query}' in authenticated portal",
                        "source": "authenticated_portal",
                        "status": "login_successful"
                    })
                else:
                    events_found.append({
                        "message": f"No specific references to '{query}' found, but authenticated access successful",
                        "source": "authenticated_portal", 
                        "status": "login_successful"
                    })
                
                return json.dumps(events_found, indent=2)
            else:
                return f"Login successful but couldn't access dashboard: {events_response.status_code}"
        else:
            return f"Login failed with status: {response.status_code}"
            
    except Exception as e:
        return f"Authentication error: {str(e)}"

if __name__ == "__main__":
    result = scrape_brella_authenticated("Mashup 2025")
    print(result)