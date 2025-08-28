#!/usr/bin/env python3

from tools.brella_auth_scraper import BrellaAuthScraper
import os
from dotenv import load_dotenv

load_dotenv()

def test_brella_auth():
    """Test the authenticated Brella scraper"""
    
    # Check if credentials are set
    if not os.getenv("BRELLA_EMAIL") or not os.getenv("BRELLA_PASSWORD"):
        print("Please set BRELLA_EMAIL and BRELLA_PASSWORD in your .env file")
        return
    
    print("Testing Brella authenticated scraper...")
    
    scraper = BrellaAuthScraper()
    
    # Test login
    print("Attempting login...")
    if scraper.login():
        print("✓ Login successful!")
        
        # Test event scraping
        print("Scraping events...")
        result = scraper.run("Mashup 2025")
        print("Results:")
        print(result)
        
    else:
        print("✗ Login failed. Please check your credentials.")

if __name__ == "__main__":
    test_brella_auth()