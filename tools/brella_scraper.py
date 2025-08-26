from crewai.tools import BaseTool
import requests
from bs4 import BeautifulSoup
import os, time, json
from typing import Dict, Optional
from pydantic import BaseModel, Field

class BrellaScraperSchema(BaseModel):
    search_term: str = Field(..., description="The term to search for on Brella.io")
    category: str = Field(default="all", description="Category to filter results (e.g., 'events', 'people', 'companies')")

class BrellaScraper(BaseTool):
    name: str = "Brella Scraper"
    description: str = "Scrapes Brella.io website for event and networking information."
    args_schema: type[BaseModel] = BrellaScraperSchema
    
    def _run(self, search_term: str, category: str = "all"):
        """
        Scrape Brella.io website for information based on search term and category.
        
        Args:
            search_term: The term to search for on Brella.io
            category: Optional category to filter results (e.g., "events", "people", "companies")
        
        Returns:
            Structured information from Brella.io
        """
        
        if category == "all" and "category" in search_term.lower():
            
            if "category 'events'" in search_term.lower():
                category = "events"
            elif "category 'companies'" in search_term.lower():
                category = "companies"
            elif "category 'people'" in search_term.lower():
                category = "people"
            elif "category 'networking'" in search_term.lower():
                category = "networking"
        try:
            
            serper_api_key = os.getenv("SERPER_API_KEY")
            if serper_api_key:
                brella_info = self._search_with_serper(search_term, category, serper_api_key)
                if brella_info:
                    return brella_info
            
            
            brella_info = self._scrape_brella_directly(search_term, category)
            if brella_info:
                return brella_info
            
            return "No information found on Brella.io for the given search term."
        except Exception as e:
            print(f"Error in Brella scraper: {str(e)}")
            return f"Error: Could not scrape Brella.io - {str(e)}"
    
    def _search_with_serper(self, search_term: str, category: str, api_key: str) -> Optional[str]:
        """Search using Serper API to find Brella.io content"""
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": f"site:brella.io {search_term} {category}",
                "gl": "us",
                "hl": "en",
                "num": 10
            })
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
                
                results = []
                
                if 'organic' in data:
                    for result in data['organic']:
                        title = result.get('title', '')
                        link = result.get('link', '')
                        snippet = result.get('snippet', '')
                        
                        if 'brella.io' in link:
                           
                            page_content = self._get_page_content(link)
                            
                            results.append({
                                "title": title,
                                "url": link,
                                "description": snippet,
                                "content": page_content
                            })
                
                if results:
                    return json.dumps(results, indent=2)
            
            return None
        except Exception as e:
            print(f"Serper API error: {str(e)}")
            return None
    
    def _scrape_brella_directly(self, search_term: str, category: str) -> Optional[str]:
        """Directly scrape Brella.io website"""
        try:

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
          
            main_url = "https://www.brella.io/"
            main_response = requests.get(main_url, headers=headers)
            
            results = {
                "main_site_info": {},
                "search_results": []
            }
            
       
            if main_response.status_code == 200:
                soup = BeautifulSoup(main_response.text, 'html.parser')
                
                results["main_site_info"] = {
                    "title": soup.title.text if soup.title else "Brella.io",
                    "description": self._extract_meta_description(soup),
                    "features": self._extract_features(soup)
                }
                
                relevant_links = self._find_relevant_links(soup, search_term)
                
                for link in relevant_links[:5]: 
                    if link.startswith('/'):
                        link = main_url.rstrip('/') + link
                    elif not link.startswith('http'):
                        link = main_url.rstrip('/') + '/' + link
                    
                    page_info = self._get_page_info(link, headers, search_term)
                    if page_info:
                        results["search_results"].append(page_info)
            
            if not results["search_results"] and category != "all":
                search_url = f"https://www.brella.io/search?q={search_term}&category={category}"
                search_results = self._process_search_page(search_url, headers)
                if search_results:
                    results["search_results"].extend(search_results)
            
            return json.dumps(results, indent=2)
        except Exception as e:
            print(f"Direct scraping error: {str(e)}")
            return None
    
    def _extract_meta_description(self, soup):
        """Extract meta description from the page"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        return "No description available"
    
    def _extract_features(self, soup):
        """Extract features or key points from the Brella.io homepage"""
        features = []
        
        feature_sections = soup.select('.feature, .features, .benefits, .services')
        if feature_sections:
            for section in feature_sections:
                feature_items = section.select('h2, h3, h4')
                for item in feature_items:
                    features.append(item.text.strip())
        
        if not features:
            list_items = soup.select('ul li, ol li')
            for item in list_items[:10]:  
                features.append(item.text.strip())
        
        return features if features else ["No specific features extracted"]
    
    def _find_relevant_links(self, soup, search_term):
        """Find links that might be relevant to the search term"""
        relevant_links = []
        search_term_lower = search_term.lower()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            text = a_tag.text.strip().lower()
            
            if search_term_lower in text or search_term_lower in href.lower():
                relevant_links.append(href)
        
        return relevant_links
    
    def _get_page_info(self, url, headers, search_term):
        """Get information from a specific page"""
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                page_info = {
                    "url": url,
                    "title": soup.title.text if soup.title else "No title",
                    "description": self._extract_meta_description(soup),
                    "content_summary": self._extract_content_summary(soup, search_term)
                }
                
                return page_info
            return None
        except Exception as e:
            print(f"Error getting page info for {url}: {str(e)}")
            return None
    
    def _extract_content_summary(self, soup, search_term):
        """Extract a summary of the content, focusing on parts relevant to the search term"""
        search_term_lower = search_term.lower()
        summary = []
        
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.text.strip()
            if search_term_lower in text.lower():
                summary.append(text)
        
        if summary:
            return summary[:3]  
        
        return [p.text.strip() for p in paragraphs[:3] if p.text.strip()]
    
    def _process_search_page(self, search_url, headers):
        """Process a search results page"""
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = []
               
                result_items = soup.select('.search-result, .result-item, .card')
                
                for item in result_items:
                    title_elem = item.select_one('h2, h3, .title')
                    link_elem = item.select_one('a')
                    desc_elem = item.select_one('p, .description')
                    
                    title = title_elem.text.strip() if title_elem else "No title"
                    link = link_elem.get('href', '') if link_elem else ""
                    description = desc_elem.text.strip() if desc_elem else "No description"
                    
                    if link.startswith('/'):
                        link = "https://www.brella.io" + link
                    
                    results.append({
                        "title": title,
                        "url": link,
                        "description": description
                    })
                
                return results
            return []
        except Exception as e:
            print(f"Error processing search page: {str(e)}")
            return []
    
    def _get_page_content(self, url):
        """Get the main content from a page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                main_content = soup.select_one('main, #content, .content, article')
                
                if main_content:
                    paragraphs = main_content.find_all('p')
                    content = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
                    
                    if content:
                        return content[:1000] + "..." if len(content) > 1000 else content
                
                paragraphs = soup.find_all('p')
                content = "\n\n".join([p.text.strip() for p in paragraphs[:5] if p.text.strip()])
                
                return content[:1000] + "..." if len(content) > 1000 else content
            
            return "Could not retrieve page content"
        except Exception as e:
            print(f"Error getting page content: {str(e)}")
            return f"Error retrieving content: {str(e)}"