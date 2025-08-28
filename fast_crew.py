from crewai import Agent, Task, Crew, Process
from tools.brella_scraper import BrellaScraper

class FastBrellaResearchCrew:
    """Fast single-agent Brella Research Crew"""
    
    def __init__(self):
        self.research_agent = Agent(
            role="Brella Research Specialist",
            goal="Quickly find comprehensive information on Brella.io",
            backstory="Expert researcher who efficiently gathers events, companies, and networking data from Brella.io in one go.",
            tools=[BrellaScraper()],
            verbose=False
        )
        
        self.research_task = Task(
            description="Search Brella.io for ALL information about {search_term} including events, companies, and networking opportunities. Provide a comprehensive report covering all aspects.",
            expected_output="A complete JSON report with events, companies, and networking information all in one response.",
            agent=self.research_agent
        )
    
    def crew(self):
        return Crew(
            agents=[self.research_agent],
            tasks=[self.research_task],
            process=Process.sequential,
            verbose=False
        )