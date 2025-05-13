from crewai.tools import BaseTool
import requests, re, json, os
import time
from typing import Optional
from bs4 import BeautifulSoup

class WebsiteScraper(BaseTool):
    name: str = "Website Scraper"
    description: str = "Scrapes company websites for information."
    
    def _run(self, company_name: str):
        try:
            # First try using the Serper API for better results
            serper_api_key = os.getenv("SERPER_API_KEY")
            if serper_api_key:
                website_url = self._search_with_serper(company_name, serper_api_key)
                if website_url and self._is_valid_company_site(website_url, company_name):
                    return website_url

            # Try with DuckDuckGo
            website_url = self._search_with_duckduckgo(company_name)
            if website_url and self._is_valid_company_site(website_url, company_name):
                return website_url

            # Try with Google
            website_url = self._search_with_google(company_name)
            if website_url and self._is_valid_company_site(website_url, company_name):
                return website_url

            # If all else fails, try to guess the URL for well-known companies
            website_url = self._guess_company_url(company_name)
            if website_url:
                return website_url

            return "Not found"
        except Exception as e:
            print(f"Error in Website scraper: {str(e)}")
            return "Error: Could not find company website"
    
    def _search_with_serper(self, company_name: str, api_key: str) -> Optional[str]:
        """Search using Serper API"""
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": f"{company_name} official website",
                "gl": "us",
                "hl": "en",
                "num": 5
            })
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
                
                # Check organic results
                if 'organic' in data:
                    for result in data['organic']:
                        link = result.get('link', '')
                        if self._is_valid_company_site(link, company_name):
                            return link
            
            return None
        except Exception as e:
            print(f"Serper API error: {str(e)}")
            return None
    
    def _search_with_duckduckgo(self, company_name: str) -> Optional[str]:
        """Search using DuckDuckGo"""
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
            q = f"{company_name} official website"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get("https://duckduckgo.com/html/", params={"q": q}, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for result links
                for result in soup.select('.result__a'):
                    href = result.get('href', '')
                    if href and self._is_valid_company_site(href, company_name):
                        return href
                
                # If no good results found, try a regex search
                match = re.search(r'https?://[^"/]+\.[a-z]{2,}', html)
                if match:
                    url = match.group(0)
                    if self._is_valid_company_site(url, company_name):
                        return url
            
            return None
        except Exception as e:
            print(f"DuckDuckGo search error: {str(e)}")
            return None
    
    def _search_with_google(self, company_name: str) -> Optional[str]:
        """Search using Google"""
        try:
            query = f'"{company_name}" official website'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Look for result links
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if href.startswith('/url?q='):
                        # Extract the actual URL from Google's redirect URL
                        url = href[7:].split('&')[0]
                        if self._is_valid_company_site(url, company_name):
                            return url
            
            return None
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return None
    
    def _guess_company_url(self, company_name: str) -> Optional[str]:
        """Try to guess the company URL for well-known companies"""
        company_name_lower = company_name.lower()
        
        # Dictionary of known company websites
        known_companies = {
            "tesla": "https://www.tesla.com",
            "microsoft": "https://www.microsoft.com",
            "apple": "https://www.apple.com",
            "google": "https://www.google.com",
            "amazon": "https://www.amazon.com",
            "facebook": "https://www.facebook.com",
            "meta": "https://www.meta.com",
            "twitter": "https://www.twitter.com",
            "netflix": "https://www.netflix.com",
            "uber": "https://www.uber.com",
            "airbnb": "https://www.airbnb.com",
            "spotify": "https://www.spotify.com",
            "snapchat": "https://www.snapchat.com",
            "pinterest": "https://www.pinterest.com",
            "linkedin": "https://www.linkedin.com",
            "instagram": "https://www.instagram.com",
            "tiktok": "https://www.tiktok.com"
        }
        
        # Check if the company name is in our known list
        if company_name_lower in known_companies:
            return known_companies[company_name_lower]
        
        # Try to guess based on company name
        # Remove spaces, special characters, and common terms
        clean_name = re.sub(r'[^\w\s]', '', company_name_lower)
        clean_name = re.sub(r'\s+', '', clean_name)
        clean_name = re.sub(r'(inc|corp|llc|ltd)$', '', clean_name)
        
        # Return a guessed URL
        return f"https://www.{clean_name}.com"
    
    def _is_valid_company_site(self, url: str, company_name: str) -> bool:
        """Check if the URL is likely to be a valid company website"""
        if not url or not url.startswith('http'):
            return False
        
        # Exclude common non-company sites
        excluded_domains = [
            'wikipedia.org', 'facebook.com', 'twitter.com', 'linkedin.com',
            'instagram.com', 'youtube.com', 'amazon.com', 'ebay.com',
            'crunchbase.com', 'bloomberg.com', 'forbes.com', 'wsj.com',
            'nytimes.com', 'cnbc.com', 'reuters.com', 'ft.com',
            'sec.gov', 'nasdaq.com', 'nyse.com', 'w3.org'
        ]
        
        for domain in excluded_domains:
            if domain in url:
                return False
        
        # Check if company name is in the domain (simple heuristic)
        company_name_simple = re.sub(r'[^\w\s]', '', company_name.lower())
        company_name_simple = re.sub(r'\s+', '', company_name_simple)
        domain = url.lower().split('/')[2] if len(url.split('/')) > 2 else ''
        
        # For well-known companies with different domains
        if company_name.lower() == "tesla" and "tesla.com" in domain:
            return True
        
        # General check
        return company_name_simple in domain or domain.startswith('www.' + company_name_simple)
