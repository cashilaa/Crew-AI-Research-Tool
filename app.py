import streamlit as st
import json
import pandas as pd
from datetime import datetime
from main import research_brella
import os
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="Brella Event Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    

    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #f8f9fa;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🌐 Brella Event Intelligence</h1>', unsafe_allow_html=True)
st.markdown("### Discover founders, investors, and networking opportunities at Brella events")

# Sidebar
with st.sidebar:
    st.markdown("## 🔧 Search Configuration")
    
    # Search parameters
    search_term = st.text_input("🔍 Event/Company Name", placeholder="e.g., Mashup 2025, TechCrunch Disrupt")
    
    category = st.selectbox(
        "📂 Search Category",
        ["people", "events", "companies", "networking", "all"],
        index=0
    )
    
    attendee_type = st.selectbox(
        "👥 Attendee Type",
        ["founders", "investors", "executives", "speakers", "attendees", "all"],
        index=0
    )
    
    st.markdown("---")
    
    # Credentials status
    st.markdown("## 🔐 Authentication Status")
    
    brella_email = os.getenv("BRELLA_EMAIL")
    brella_password = os.getenv("BRELLA_PASSWORD")
    
    if brella_email and brella_password:
        st.success("✅ Authenticated Access Enabled")
        st.info(f"📧 {brella_email}")
    else:
        st.warning("⚠️ Public Access Only")
        st.info("Add BRELLA_EMAIL & BRELLA_PASSWORD to .env for authenticated access")

# Main content
if st.button("🚀 Start Research", use_container_width=True):
    if not search_term:
        st.error("Please enter a search term")
    else:
        with st.spinner(f"🔍 Researching '{search_term}' for {attendee_type}..."):
            try:
                result = research_brella(search_term, category, attendee_type)
                st.session_state.last_result = result
                st.success("✅ Research completed!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Results display
if 'last_result' in st.session_state:
    result = st.session_state.last_result
    
    st.markdown("---")
    st.markdown("## 📋 Research Results")
    
    # Create tabs for different result types
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Events", "🏢 Companies", "🤝 Networking", "👨‍💼 Founders", "👥 Attendees"])
    
    with tab1:
        st.markdown("### 🎯 Events Information")
        if result.get('events') and result['events'] != 'Not available':
            try:
                events_data = json.loads(result['events']) if isinstance(result['events'], str) else result['events']
                if isinstance(events_data, dict) and 'events' in events_data:
                    events_df = pd.DataFrame(events_data['events'])
                    st.dataframe(events_df, use_container_width=True)
                else:
                    st.json(events_data)
            except:
                st.text(result['events'])
        else:
            st.info("No events data available")
    
    with tab2:
        st.markdown("### 🏢 Companies Information")
        if result.get('companies') and result['companies'] != 'Not available':
            try:
                companies_data = json.loads(result['companies']) if isinstance(result['companies'], str) else result['companies']
                if isinstance(companies_data, list):
                    companies_df = pd.DataFrame(companies_data)
                    st.dataframe(companies_df, use_container_width=True)
                else:
                    st.json(companies_data)
            except:
                st.text(result['companies'])
        else:
            st.info("No companies data available")
    
    with tab3:
        st.markdown("### 🤝 Networking Opportunities")
        if result.get('networking') and result['networking'] != 'Not available':
            st.markdown(result['networking'])
        else:
            st.info("No networking data available")
    
    with tab4:
        st.markdown("### 👨‍💼 Founders Information")
        if result.get('founders') and result['founders'] != 'Not available':
            try:
                founders_data = json.loads(result['founders']) if isinstance(result['founders'], str) else result['founders']
                if isinstance(founders_data, list) and founders_data:
                    founders_df = pd.DataFrame(founders_data)
                    st.dataframe(founders_df, use_container_width=True)
                else:
                    st.json(founders_data)
            except:
                st.text(result['founders'])
        else:
            st.info("No founders data available")
    
    with tab5:
        st.markdown("### 👥 Event Attendees")
        if result.get('attendees') and result['attendees'] != 'Not available':
            try:
                attendees_data = json.loads(result['attendees']) if isinstance(result['attendees'], str) else result['attendees']
                if isinstance(attendees_data, list) and attendees_data:
                    attendees_df = pd.DataFrame(attendees_data)
                    st.dataframe(attendees_df, use_container_width=True)
                else:
                    st.json(attendees_data)
            except:
                st.text(result['attendees'])
        else:
            st.info("No attendees data available")
    
    # Download results
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download JSON", use_container_width=True):
            st.download_button(
                label="💾 Download Results",
                data=json.dumps(result, indent=2),
                file_name=f"brella_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export to CSV", use_container_width=True):
            # Create a simplified CSV export
            csv_data = {
                'Search Term': [result.get('search_term', '')],
                'Category': [result.get('category', '')],
                'Attendee Type': [result.get('attendee_type', '')],
                'Timestamp': [result.get('timestamp', '')],
                'Events Found': ['Yes' if result.get('events') != 'Not available' else 'No'],
                'Companies Found': ['Yes' if result.get('companies') != 'Not available' else 'No'],
                'Founders Found': ['Yes' if result.get('founders') != 'Not available' else 'No'],
                'Attendees Found': ['Yes' if result.get('attendees') != 'Not available' else 'No']
            }
            csv_df = pd.DataFrame(csv_data)
            st.download_button(
                label="📊 Download CSV",
                data=csv_df.to_csv(index=False),
                file_name=f"brella_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🔄 Clear Results", use_container_width=True):
            if 'last_result' in st.session_state:
                del st.session_state.last_result
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🌐 <strong>Brella Event Intelligence</strong> | Powered by CrewAI & OpenAI</p>
        <p>Discover networking opportunities and connect with founders, investors, and industry leaders</p>
    </div>
    """, 
    unsafe_allow_html=True
)