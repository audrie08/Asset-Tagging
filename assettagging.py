import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

# Custom CSS for modern, sophisticated design
st.markdown("""
<style>
    /* Global styles */
    .main {
        padding: 2rem;
        background: #fafafa;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Title styling */
    h1 {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px;
        padding: 0 24px;
        font-weight: 600;
        font-size: 14px;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #f5f5f5;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
        color: white !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e5e5e5;
        padding: 12px 16px;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #333;
        box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
    }
    
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #e5e5e5;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
    }
    
    [data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
    }
    
    /* Expander styling - Main asset names */
    .streamlit-expanderHeader {
        background: white !important;
        border: 2px solid #e5e5e5 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        margin-bottom: 8px !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #333 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        transform: translateY(-1px);
    }
    
    [data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
        margin-bottom: 12px;
    }
    
    .streamlit-expanderContent {
        background: #fafafa !important;
        border: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 16px !important;
        margin-top: -8px !important;
    }
    
    /* Nested expanders for asset codes */
    .streamlit-expanderContent .streamlit-expanderHeader {
        background: white !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        margin-bottom: 8px !important;
    }
    
    .streamlit-expanderContent .streamlit-expanderHeader:hover {
        background: #f9f9f9 !important;
        border-color: #999 !important;
    }
    
    .streamlit-expanderContent .streamlit-expanderContent {
        background: white !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin-top: -8px !important;
    }
    
    /* Detail rows */
    .detail-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .detail-row:last-child {
        border-bottom: none;
    }
    
    .detail-label {
        color: #666;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .detail-value {
        font-weight: 600;
        font-size: 14px;
        color: #1a1a1a;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: #1a1a1a;
        color: white;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: #333;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }
    
    /* Caption text */
    .css-1629p8f, [data-testid="stCaptionContainer"] {
        color: #666;
        font-size: 13px;
        margin-bottom: 1.5rem;
    }
    
    /* Column spacing */
    [data-testid="column"] {
        padding: 0 6px;
    }
    
    /* Remove extra padding */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_credentials():
    try:
        credentials_dict = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            "private_key": st.secrets["google_credentials"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["google_credentials"]["client_email"],
            "client_id": st.secrets["google_credentials"]["client_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    except Exception as e:
        st.error(f"Error loading credentials: {e}")
        return None

@st.cache_data(ttl=300)
def load_sheet_data(_credentials, sheet_url, sheet_index=0):
    try:
        client = gspread.authorize(_credentials)
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.get_worksheet(sheet_index)
        data = worksheet.get_all_values()
        
        if not data or len(data) < 4:
            return pd.DataFrame()
        
        row1_headers = data[1]
        row2_headers = data[2]
        
        combined_headers = []
        for i in range(len(row1_headers)):
            header1 = row1_headers[i].strip() if i < len(row1_headers) else ''
            header2 = row2_headers[i].strip() if i < len(row2_headers) else ''
            
            if header1 and header2:
                combined = f"{header1} {header2}"
            elif header1:
                combined = header1
            elif header2:
                combined = header2
            else:
                combined = 'Unnamed'
            
            combined_headers.append(combined)
        
        unique_headers = []
        header_counts = {}
        
        for header in combined_headers:
            if header in header_counts:
                header_counts[header] += 1
                unique_headers.append(f"{header}_{header_counts[header]}")
            else:
                header_counts[header] = 0
                unique_headers.append(header)
        
        df = pd.DataFrame(data[3:], columns=unique_headers)
        return df
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        return pd.DataFrame()

def display_asset_details(row, columns):
    """Display individual asset details"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div class="detail-row"><span class="detail-label">Asset Number</span><span class="detail-value">{row.get(columns[0], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Asset Name</span><span class="detail-value">{row.get(columns[3], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Quantity</span><span class="detail-value">{row.get(columns[4], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">{row.get(columns[2], "N/A")}</span></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="detail-row"><span class="detail-label">Station</span><span class="detail-value">{row.get(columns[1], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Length (cm)</span><span class="detail-value">{row.get(columns[5], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Width (cm)</span><span class="detail-value">{row.get(columns[6], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Height (cm)</span><span class="detail-value">{row.get(columns[7], "N/A")}</span></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="detail-row"><span class="detail-label">Rated Voltage</span><span class="detail-value">{row.get(columns[9], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Power</span><span class="detail-value">{row.get(columns[10], "N/A")}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">{row.get(columns[11], "N/A")}</span></div>', unsafe_allow_html=True)

# Main App
st.title("🏷️ Asset Tagging System")
st.markdown("Manage and track all commissary assets")

credentials = load_credentials()

if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)
    
    if not df.empty:
        # Remove Column A (index 0 - Unnamed)
        df = df.drop(df.columns[0], axis=1)
        
        # Update column indices after removing column A
        station_col = df.columns[1]  # Station (was index 2, now index 1)
        asset_name_col = df.columns[3]  # Asset Name (was index 4, now index 3)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Assets", len(df))
        with col2:
            working_count = len(df[df[df.columns[11]].str.contains("Working", case=False, na=False)])
            st.metric("Working", working_count)
        with col3:
            not_working = len(df[df[df.columns[11]].str.contains("Not Working", case=False, na=False)])
            st.metric("Not Working", not_working)
        
        st.markdown("---")
        
        # Define stations
        stations = {
            'Hot Station': 'Hot Station',
            'Fabrication Station': 'Fabrication Station',
            'Pastry Station': 'Pastry Station',
            'Packing Station': 'Packing Station'
        }
        
        # Create tabs
        tabs = st.tabs(list(stations.keys()))
        
        # Filter and display data for each station
        for tab, (tab_name, station_value) in zip(tabs, stations.items()):
            with tab:
                # Filter by station
                station_df = df[df[station_col] == station_value]
                
                if not station_df.empty:
                    # Search and filter section
                    col_search, col_filter = st.columns([2, 1])
                    
                    with col_search:
                        search_term = st.text_input("🔍 Search assets", placeholder="Type to search...", key=f"search_{station_value}")
                    
                    with col_filter:
                        asset_names = ['All'] + sorted(station_df[asset_name_col].unique().tolist())
                        selected_asset = st.selectbox("Filter by Asset Name", options=asset_names, key=f"filter_{station_value}")
                    
                    # Apply filters
                    filtered = station_df.copy()
                    
                    if selected_asset != 'All':
                        filtered = filtered[filtered[asset_name_col] == selected_asset]
                    
                    if search_term:
                        mask = filtered[asset_name_col].str.contains(search_term, case=False, na=False)
                        filtered = filtered[mask]
                    
                    st.caption(f"Showing {len(filtered)} of {len(station_df)} assets")
                    
                    # Display assets as cards
                    if not filtered.empty:
                        # Group by Asset Name
                        grouped = filtered.groupby(asset_name_col)
                        asset_groups = list(grouped)
                        
                        # Display in 5 columns
                        num_cols = 5
                        for i in range(0, len(asset_groups), num_cols):
                            cols = st.columns(num_cols)
                            
                            # Get the batch of asset groups for this row
                            batch = asset_groups[i:i + num_cols]
                            
                            for col_idx, (asset_name, group_df) in enumerate(batch):
                                with cols[col_idx]:
                                    # First level expander - Asset Name with count
                                    with st.expander(f"📋 {asset_name} ({len(group_df)})"):
                                        # Second level - Individual asset codes
                                        for idx, row in group_df.iterrows():
                                            asset_number = row.get(df.columns[0], 'N/A')
                                            with st.expander(f"🔖 {asset_number}"):
                                                display_asset_details(row, df.columns)
                    else:
                        st.info("No assets found matching your filters.")
                    
                    # Download button
                    st.markdown("---")
                    csv = filtered.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {tab_name} Data (CSV)",
                        data=csv,
                        file_name=f"{station_value.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"btn_{station_value}"
                    )
                else:
                    st.warning(f"No assets found for {station_value}")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
