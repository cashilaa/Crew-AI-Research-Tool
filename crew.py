from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
from tools.brella_scraper import BrellaScraper

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
    
    def crew(self):
        """Creates the Brella research crew"""
        return Crew(
            agents=[
                self.event_agent,
                self.company_agent,
                self.networking_agent
            ],
            tasks=[
                self.event_task,
                self.company_task,
                self.networking_task
            ],
            process=Process.sequential,
            verbose=True
        )
