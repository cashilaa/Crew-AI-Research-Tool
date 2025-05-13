from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
from tools.linkedin_scraper import LinkedInScraper
from tools.website_scraper import WebsiteScraper

class CompanyResearchCrew:
    """Company Research Crew for finding information about companies and founders"""
    
    def __init__(self):
        # Create agents
        self.linkedin_agent = Agent(
            role="LinkedIn Research Specialist",
            goal="Find public LinkedIn profile URLs for founders and companies",
            backstory="OSINT professional fluent in advanced LinkedIn search operators.",
            tools=[LinkedInScraper()],
            verbose=True
        )
        
        self.info_agent = Agent(
            role="Company Information Analyst",
            goal="Compile a concise overview of companies",
            backstory="Analyst experienced with official filings, press releases and Crunchbase data.",
            verbose=True
        )
        
        self.site_agent = Agent(
            role="Website Finder",
            goal="Locate the verified corporate domain for companies",
            backstory="Guru of WHOIS look-ups and result-ranking heuristics.",
            tools=[WebsiteScraper()],
            verbose=True
        )
        
        # Create tasks
        self.linkedin_task = Task(
            description="Search LinkedIn and return founder profile URL(s) for {founder_name} of {company_name}.",
            expected_output="A list of valid https://www.linkedin.com/in/... links.",
            agent=self.linkedin_agent
        )
        
        self.company_info_task = Task(
            description="Collect company mission, founding year, HQ location and core product lines for {company_name}.",
            expected_output="A 150-word markdown paragraph with citations.",
            agent=self.info_agent
        )
        
        self.website_task = Task(
            description="Provide the official website (or GitHub repo for OSS orgs) for {company_name}.",
            expected_output="A single https:// URL.",
            agent=self.site_agent
        )
    
    def crew(self):
        """Creates the company research crew"""
        return Crew(
            agents=[
                self.linkedin_agent,
                self.info_agent,
                self.site_agent
            ],
            tasks=[
                self.linkedin_task,
                self.company_info_task,
                self.website_task
            ],
            process=Process.sequential,
            verbose=True
        )
