from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
from tools.brella_scraper import BrellaScraper
from tools.brella_auth_scraper import BrellaAuthScraper

class BrellaResearchCrew:
    """Brella Research Crew for finding information on Brella.io website"""
    
    def __init__(self):
        # Create agents
        self.event_agent = Agent(
            role="Brella Event Specialist",
            goal="Find event information on Brella.io",
            backstory="Expert in discovering and analyzing networking events on Brella.io platform.",
            tools=[BrellaScraper()],
            verbose=True
        )
        
        self.company_agent = Agent(
            role="Brella Company Analyst",
            goal="Research companies participating in Brella events",
            backstory="Analyst specialized in gathering information about companies using the Brella platform.",
            tools=[BrellaScraper()],
            verbose=True
        )
        
        self.networking_agent = Agent(
            role="Brella Networking Specialist",
            goal="Analyze networking opportunities on Brella.io",
            backstory="Expert in identifying valuable networking connections and opportunities on Brella.",
            tools=[BrellaScraper()],
            verbose=True
        )
        
        self.founder_agent = Agent(
            role="Startup Founder Researcher",
            goal="Find startup founders and their companies at Brella events",
            backstory="Specialist in identifying startup founders, their companies, and business fields at networking events.",
            tools=[BrellaScraper()],
            verbose=True
        )
        
        self.attendee_agent = Agent(
            role="Event Attendee Researcher",
            goal="Find specific types of people (founders, investors, executives) at specific Brella events",
            backstory="Expert in researching event attendees, their roles, companies, and professional backgrounds at Brella events.",
            tools=[BrellaScraper(), BrellaAuthScraper()],
            verbose=True
        )
        
        # Create tasks
        self.event_task = Task(
            description="Search Brella.io for information about events related to {search_term}. Use category 'events'.",
            expected_output="A detailed JSON report about events, including dates, locations, and descriptions.",
            agent=self.event_agent
        )
        
        self.company_task = Task(
            description="Find companies on Brella.io related to {search_term}. Use category 'companies'.",
            expected_output="A JSON list of companies with their profiles and participation in Brella events.",
            agent=self.company_agent
        )
        
        self.networking_task = Task(
            description="Analyze networking opportunities on Brella.io for {search_term}. Use category 'networking'.",
            expected_output="A comprehensive report on networking features and opportunities available.",
            agent=self.networking_agent
        )
        
        self.founder_task = Task(
            description="Search for startup founders and entrepreneurs at Brella events related to {search_term}. Find their company names, business fields, and roles. Use category 'people'.",
            expected_output="A JSON list of startup founders with their company names, business fields, roles, and event participation details.",
            agent=self.founder_agent
        )
        
        self.attendee_task = Task(
            description="Search for attendees at specific Brella events related to {search_term}. Focus on finding {attendee_type} (founders, investors, executives, speakers) with their names, companies, roles, and professional backgrounds. Use both public Brella pages and authenticated portal access.",
            expected_output="A detailed JSON list of event attendees with names, companies, roles, business fields, and contact information where available.",
            agent=self.attendee_agent
        )
    
    def crew(self):
        """Creates the Brella research crew"""
        return Crew(
            agents=[
                self.event_agent,
                self.company_agent,
                self.networking_agent,
                self.founder_agent,
                self.attendee_agent
            ],
            tasks=[
                self.event_task,
                self.company_task,
                self.networking_task,
                self.founder_task,
                self.attendee_task
            ],
            process=Process.sequential,
            verbose=True
        )
