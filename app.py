import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Lazy import to avoid startup errors
def get_crew_instance():
    try:
        from fast_crew import FastBrellaResearchCrew
        return FastBrellaResearchCrew()
    except Exception as e:
        st.error(f"Error importing CrewAI: {str(e)}")
        st.error("Please ensure all dependencies are properly installed.")
        return None

def get_sheets_exporter(spreadsheet_url):
    try:
        from tools.google_sheets_exporter import GoogleSheetsExporter
        return GoogleSheetsExporter(spreadsheet_url=spreadsheet_url)
    except Exception as e:
        st.error(f"Error importing Google Sheets exporter: {str(e)}")
        return None

st.set_page_config(page_title="Brella.io Research Tool", page_icon="🔍", layout="wide")

st.title("🔍 Brella.io Research Tool")
st.markdown("Scrape and analyze information from Brella.io networking platform")

# Sidebar for configuration
st.sidebar.header("Configuration")

# API Keys check
openai_key = st.sidebar.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
serper_key = st.sidebar.text_input("Serper API Key", value=os.getenv("SERPER_API_KEY", ""), type="password")

if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key
if serper_key:
    os.environ["SERPER_API_KEY"] = serper_key

# Google Sheets configuration
st.sidebar.subheader("Google Sheets Export (Optional)")
export_to_sheets = st.sidebar.checkbox("Export to Google Sheets")
spreadsheet_url = st.sidebar.text_input("Spreadsheet URL", value=os.getenv("GOOGLE_SPREADSHEET_URL", ""))

# Main interface
tab1, tab2 = st.tabs(["Single Search", "Bulk CSV Upload"])

with tab1:
    st.header("Single Search")
    
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search Term", placeholder="e.g., tech conference")
    with col2:
        category = st.selectbox("Category", ["all", "events", "companies", "people", "networking"])
    
    if st.button("Start Research", type="primary"):
        if not openai_key:
            st.error("Please provide OpenAI API Key")
        elif not search_term:
            st.error("Please enter a search term")
        else:
            with st.spinner(f"Researching '{search_term}' on Brella.io..."):
                try:
                    crew_instance = get_crew_instance()
                    if not crew_instance:
                        st.stop()
                    crew = crew_instance.crew()
                    
                    search_with_category = f"{search_term} (category: {category})"
                    result = crew.kickoff(inputs={"search_term": search_with_category})
                    
                    # Parse the single comprehensive result
                    result_text = crew_instance.research_task.output.raw if hasattr(crew_instance.research_task, 'output') else str(result)
                    
                    output = {
                        "search_term": search_term,
                        "category": category,
                        "events": result_text,
                        "companies": result_text,
                        "networking": result_text,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.success("Research completed!")
                    
                    # Display results
                    st.subheader("Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Events**")
                        st.text_area("", output["events"], height=200, key="events")
                    with col2:
                        st.markdown("**Companies**")
                        st.text_area("", output["companies"], height=200, key="companies")
                    with col3:
                        st.markdown("**Networking**")
                        st.text_area("", output["networking"], height=200, key="networking")
                    
                    # Download JSON
                    json_str = json.dumps([output], indent=2)
                    st.download_button(
                        "Download JSON",
                        json_str,
                        f"brella_research_{search_term.replace(' ', '_')}.json",
                        "application/json"
                    )
                    
                    # Export to Google Sheets
                    if export_to_sheets and spreadsheet_url:
                        try:
                            sheets_exporter = get_sheets_exporter(spreadsheet_url)
                            if sheets_exporter.authenticate():
                                sheets_exporter.export_to_sheet([output], "Brella Research Results")
                                st.success("Results exported to Google Sheets!")
                            else:
                                st.error("Failed to authenticate with Google Sheets")
                        except Exception as e:
                            st.error(f"Google Sheets export failed: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Research failed: {str(e)}")

with tab2:
    st.header("Bulk CSV Upload")
    st.markdown("Upload a CSV file with columns: 'Search Term' and 'Category'")
    
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
        
        if st.button("Process CSV", type="primary"):
            if not openai_key:
                st.error("Please provide OpenAI API Key")
            else:
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, row in df.iterrows():
                    search_term = row.get('Search Term', '')
                    category = row.get('Category', 'all')
                    
                    status_text.text(f"Processing: {search_term}")
                    
                    try:
                        crew_instance = get_crew_instance()
                        if not crew_instance:
                            continue
                        crew = crew_instance.crew()
                        
                        search_with_category = f"{search_term} (category: {category})"
                        result = crew.kickoff(inputs={"search_term": search_with_category})
                        
                        # Parse the single comprehensive result
                        result_text = crew_instance.research_task.output.raw if hasattr(crew_instance.research_task, 'output') else str(result)
                        
                        output = {
                            "search_term": search_term,
                            "category": category,
                            "events": result_text,
                            "companies": result_text,
                            "networking": result_text,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        results.append(output)
                        
                    except Exception as e:
                        st.error(f"Error processing '{search_term}': {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(df))
                
                status_text.text("Processing complete!")
                
                # Display results summary
                st.subheader("Results Summary")
                results_df = pd.DataFrame(results)
                st.dataframe(results_df[['search_term', 'category', 'timestamp']])
                
                # Download results
                json_str = json.dumps(results, indent=2)
                st.download_button(
                    "Download All Results",
                    json_str,
                    f"brella_bulk_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
                
                # Export to Google Sheets
                if export_to_sheets and spreadsheet_url:
                    try:
                        sheets_exporter = get_sheets_exporter(spreadsheet_url)
                        if sheets_exporter.authenticate():
                            sheets_exporter.export_to_sheet(results, "Brella Research Results")
                            st.success("All results exported to Google Sheets!")
                        else:
                            st.error("Failed to authenticate with Google Sheets")
                    except Exception as e:
                        st.error(f"Google Sheets export failed: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit • Powered by CrewAI")