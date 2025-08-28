from crewai.tools import BaseTool
import requests
import json
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class BrellaAuthScraperSchema(BaseModel):
    search_term: str = Field(..., description="The term to search for on authenticated Brella portal")
    category: str = Field(default="all", description="Category to filter results")

class BrellaAuthScraper(BaseTool):
    name: str = "Brella Authenticated Scraper"
    description: str = "Scrapes events and attendee data from authenticated Brella portal"
    args_schema: type[BaseModel] = BrellaAuthScraperSchema
    
    def _run(self, search_term: str, category: str = "all") -> str:
        try:
            session = requests.Session()
            base_url = "https://next.brella.io"
            
            email = os.getenv("BRELLA_EMAIL")
            password = os.getenv("BRELLA_PASSWORD")
            
            if not email or not password:
                return json.dumps([{"error": "Authentication credentials not found"}])
            
            if self.perform_login(session, base_url, email, password):
                return self.scrape_authenticated_events(session, base_url, search_term)
            else:
                return json.dumps([{"error": "Authentication failed"}])
        except Exception as e:
            return json.dumps([{"error": f"Scraping error: {str(e)}"}])

    def perform_login(self, session, base_url, email, password) -> bool:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            login_url = f"{base_url}/login"
            response = session.get(login_url, headers=headers)
            
            if response.status_code != 200:
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token = None
            
            csrf_inputs = soup.find_all('input', {'type': 'hidden'})
            for inp in csrf_inputs:
                name = inp.get('name', '').lower()
                if 'csrf' in name or '_token' in name:
                    csrf_token = inp.get('value')
                    break
            
            login_data = {'email': email, 'password': password}
            if csrf_token:
                login_data['_token'] = csrf_token
            
            login_response = session.post(login_url, data=login_data, headers=headers)
            
            if login_response.status_code == 200:
                response_text = login_response.text.lower()
                return any(indicator in response_text for indicator in ['dashboard', 'events', 'logout'])
            
            return False
        except:
            return False

    def scrape_authenticated_events(self, session, base_url, query: str) -> str:
        try:
            events_data = []
            endpoints = [f"{base_url}/dashboard", f"{base_url}/events"]
            
            for endpoint in endpoints:
                try:
                    response = session.get(endpoint)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_text = soup.get_text().lower()
                        
                        if query.lower() in page_text:
                            attendees = self.extract_people_from_page(soup)
                            events_data.append({
                                'event': f'Event containing "{query}"',
                                'attendees': attendees,
                                'source': 'authenticated_portal',
                                'url': endpoint
                            })
                except:
                    continue
            
            if not events_data:
                events_data = [{
                    'message': f'Authenticated access successful for "{query}"',
                    'status': 'logged_in',
                    'attendees': []
                }]
            
            return json.dumps(events_data, indent=2)
        except Exception as e:
            return json.dumps([{"error": str(e)}])

    def extract_people_from_page(self, soup) -> list:
        try:
            people = []
            selectors = ['.attendee', '.participant', '.member', '.person', '.user-card']
            
            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    name = self.get_text_from_selectors(elem, ['.name', 'h3', 'h4'])
                    company = self.get_text_from_selectors(elem, ['.company', '.organization'])
                    role = self.get_text_from_selectors(elem, ['.role', '.position', '.title'])
                    
                    if name:
                        people.append({'name': name, 'company': company, 'role': role})
            
            return people[:20]
        except:
            return []

    def get_text_from_selectors(self, element, selectors: list) -> str:
        for selector in selectors:
            elem = element.select_one(selector)
            if elem:
                text = elem.get_text().strip()
                if text:
                    return text
        return ''