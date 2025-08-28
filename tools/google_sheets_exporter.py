import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import pandas as pd
from datetime import datetime
import re

class GoogleSheetsExporter:
    """
    A tool for exporting data to Google Sheets.
    """
    
    def __init__(self, spreadsheet_url=None, credentials_file=None):
        """
        Initialize the Google Sheets exporter.
        
        Args:
            spreadsheet_url: Direct URL to a Google Spreadsheet.
                             If None, will look for GOOGLE_SPREADSHEET_URL in environment variables.
            credentials_file: Path to the Google API credentials JSON file.
                              If None, will look for GOOGLE_CREDENTIALS_PATH in environment variables.
        """
        self.spreadsheet_url = spreadsheet_url or os.getenv("GOOGLE_SPREADSHEET_URL")
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        self.spreadsheet_id = None
        
        if self.spreadsheet_url:
            self.spreadsheet_id = self._extract_spreadsheet_id(self.spreadsheet_url)
        
    def _extract_spreadsheet_id(self, url):
        """Extract the spreadsheet ID from a Google Sheets URL"""
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',  # Standard format
            r'key=([a-zA-Z0-9-_]+)',             # Old format with key parameter
            r'spreadsheets/d/([a-zA-Z0-9-_]+)'   # Mobile or alternate format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
        
    def authenticate(self):
        """
        Authenticate with Google Sheets API.
        
        Returns:
            True if authentication was successful, False otherwise.
        """
        try:
            
            if self.credentials_file:
                if not os.path.exists(self.credentials_file):
                    print(f"Error: Credentials file not found at {self.credentials_file}")
                    return False
                    
                credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, self.scope)
                self.client = gspread.authorize(credentials)
                return True
            
           
            elif self.spreadsheet_url and self.spreadsheet_id:

                self.client = gspread.Client(None)
              
                try:
                    self.client.open_by_key(self.spreadsheet_id)
                    return True
                except Exception as e:
                    print(f"Error accessing spreadsheet: {str(e)}")
                    print("Make sure the spreadsheet is publicly accessible with edit permissions.")
                    return False
            
            print("Error: No credentials file or valid spreadsheet URL provided.")
            print("Set GOOGLE_CREDENTIALS_PATH or GOOGLE_SPREADSHEET_URL environment variable.")
            return False
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False
    
    def export_to_sheet(self, data, spreadsheet_name=None, worksheet_name=None):
        """
        Export data to a Google Sheet.
        
        Args:
            data: JSON data or list of dictionaries to export
            spreadsheet_name: Name of the Google Spreadsheet (only used if not using direct URL)
            worksheet_name: Name of the worksheet (optional, defaults to current date)
            
        Returns:
            URL of the spreadsheet if successful, None otherwise
        """
        try:
            if not self.client and not self.authenticate():
                return None
            
           
            if self.spreadsheet_id:
                try:
                    spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                except Exception as e:
                    print(f"Error opening spreadsheet: {str(e)}")
                    return None
            else:
                
                try:
                    spreadsheet = self.client.open(spreadsheet_name)
                except gspread.exceptions.SpreadsheetNotFound:
                    spreadsheet = self.client.create(spreadsheet_name)
                  
                    spreadsheet.share(None, perm_type='anyone', role='reader')
            
            
            if not worksheet_name:
                worksheet_name = datetime.now().strftime("%Y-%m-%d")
            
        
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
              
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            
            if isinstance(data, str):
               
                data = json.loads(data)
                
            df = pd.DataFrame(data)
            
           
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            
            return spreadsheet.url
            
        except Exception as e:
            print(f"Error exporting to Google Sheets: {str(e)}")
            return None
            
    def append_to_sheet(self, data, spreadsheet_name=None, worksheet_name=None):
        """
        Append data to an existing Google Sheet.
        
        Args:
            data: JSON data or list of dictionaries to append
            spreadsheet_name: Name of the Google Spreadsheet (only used if not using direct URL)
            worksheet_name: Name of the worksheet (optional, defaults to current date)
            
        Returns:
            URL of the spreadsheet if successful, None otherwise
        """
        try:
            if not self.client and not self.authenticate():
                return None
            
            if self.spreadsheet_id:
                try:
                    spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                except Exception as e:
                    print(f"Error opening spreadsheet: {str(e)}")
                    return None
            else:
                
                try:
                    spreadsheet = self.client.open(spreadsheet_name)
                except gspread.exceptions.SpreadsheetNotFound:
                
                    return self.export_to_sheet(data, spreadsheet_name, worksheet_name)
            
           
            if not worksheet_name:
                worksheet_name = datetime.now().strftime("%Y-%m-%d")
            
           
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            
            
            if isinstance(data, str):
                data = json.loads(data)
                
            df = pd.DataFrame(data)
                
            existing_data = worksheet.get_all_values()
            start_row = len(existing_data) + 1
            
            if not existing_data:
                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            else:
                worksheet.update(f'A{start_row}', df.values.tolist())
            
            return spreadsheet.url
            
        except Exception as e:
            print(f"Error appending to Google Sheets: {str(e)}")
            return None