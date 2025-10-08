import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container styling */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Header Section - Yellow Background */
    .main > div:first-child {
        background: linear-gradient(135deg, #FFD700 0%, #FFC107 100%);
        border-bottom: 4px solid #1a1a1a;
        padding: 2.5rem 3rem !important;
        margin: 0 !important;
    }
    
    [data-testid="column"] {padding: 0 8px;}
    
    /* Header styling */
    .header-title {
        font-size: 32px;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .header-subtitle {
        font-size: 14px;
        color: #333;
        font-weight: 500;
        margin-bottom: 0;
    }
    
    /* Content padding */
    .content-wrapper {
        padding: 2rem 3rem;
    }
    
    /* Tabs - Gray Container with Black Active */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #e0e0e0;
        padding: 0.5rem;
        border-radius: 12px;
        border: none;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 0 24px;
        font-weight: 600;
        font-size: 14px;
        color: #666;
        border: none;
        background: transparent;
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #ccc;
        color: #1a1a1a;
    }
    .stTabs [aria-selected="true"] {
        background: #1a1a1a !important;
        color: #FFD700 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Metrics - Black Background with Yellow Values */
    [data-testid="stMetric"] {
        background: #1a1a1a;
        padding: 2rem 1.5rem;
        border-radius: 12px;
        border: 3px solid #FFD700;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: #FFD700;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(255, 215, 0, 0.4);
        border-color: #FFA500;
    }
    [data-testid="stMetricValue"] {
        font-size: 36px;
        font-weight: 700;
        color: #FFD700;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px;
        font-weight: 600;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Filter Section */
    .filter-section {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    /* Input fields - Black borders */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #1a1a1a !important;
    }
    .stSelectbox > div > div:hover,
    .stSelectbox > div > div:focus-within {
        border-color: #FFD700 !important;
        box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.2);
    }
    .stSelectbox label {
        font-weight: 600 !important;
        color: #1a1a1a !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 14px !important;
    }
    
    /* Buttons - Yellow Background */
    .stButton > button {
        background: #FFD700 !important;
        border: 3px solid #1a1a1a !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        text-align: center !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
        transition: all 0.2s ease !important;
        height: auto !important;
        margin-top: 8px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        background: #1a1a1a !important;
        border-color: #FFD700 !important;
        color: #FFD700 !important;
        box-shadow: 0 4px 16px rgba(255, 215, 0, 0.4) !important;
    }
    
    /* Expander styling - Black header with Yellow accents */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        border: 3px solid #1a1a1a !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        margin-bottom: 12px !important;
        color: white !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #FFD700 0%, #FFC107 100%) !important;
        color: #1a1a1a !important;
        border-color: #FFD700 !important;
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.2) !important;
    }
    
    [data-testid="stExpander"] {
        border: none !important;
        background: white;
        border-radius: 12px;
        overflow: hidden;
    }
    
    .streamlit-expanderContent {
        background: #f5f5f5 !important;
        border: none !important;
        border-top: 3px solid #FFD700 !important;
        padding: 20px !important;
    }
    
    /* Detail items in expander */
    .streamlit-expanderContent [data-testid="column"] > div {
        background: white !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 2px solid #e0e0e0 !important;
        margin-bottom: 1rem !important;
    }
    
    .streamlit-expanderContent strong {
        color: #1a1a1a !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 12px !important;
    }
    
    /* Card styling */
    .asset-card {
        background: white;
        border: 3px solid #1a1a1a;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        margin-bottom: 20px;
    }
    
    .asset-card:hover {
        box-shadow: 0 12px 32px rgba(255, 215, 0, 0.3);
        transform: translateY(-6px);
        border-color: #FFD700;
    }
    
    .asset-card-header {
        background: #1a1a1a;
        padding: 1rem 1.25rem;
        border-bottom: 3px solid #FFD700;
        transition: all 0.3s ease;
    }
    
    .asset-card:hover .asset-card-header {
        background: #FFD700;
    }
    
    .asset-card:hover .asset-name {
        color: #1a1a1a !important;
    }
    
    .asset-name {
        font-size: 18px;
        font-weight: 700;
        color: #FFD700;
        line-height: 1.3;
        margin: 0;
        transition: color 0.3s ease;
    }
    
    .asset-card-body {
        padding: 1.25rem;
    }
    
    .asset-count {
        font-size: 14px;
        font-weight: 600;
        color: #666;
        margin-bottom: 1rem;
    }
    
    .asset-footer {
        padding-top: 1rem;
        border-top: 2px solid #f0f0f0;
        font-size: 13px;
        font-weight: 700;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: color 0.2s ease;
    }
    
    .asset-card:hover .asset-footer {
        color: #FFD700;
    }
    
    /* Modal header */
    .modal-header {
        font-size: 24px;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 4px solid #FFD700;
    }
    
    .modal-count {
        color: #666;
        font-weight: 600;
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

# Main App
st.markdown('<div class="header-title">Assets</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">List of assets in the commissary</div>', unsafe_allow_html=True)

# Add spacing after header
st.markdown('<div style="margin-bottom: 2rem;"></div>', unsafe_allow_html=True)

credentials = load_credentials()

if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)
    
    if not df.empty:
        df = df.drop(df.columns[0], axis=1)
        
        station_col = df.columns[1]
        asset_name_col = df.columns[3]
        
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
        
        stations = {
            'Hot Station': 'Hot Station',
            'Fabrication Station': 'Fabrication Station',
            'Pastry Station': 'Pastry Station',
            'Packing Station': 'Packing Station'
        }
        
        tabs = st.tabs(list(stations.keys()))
        
        for tab, (tab_name, station_value) in zip(tabs, stations.items()):
            with tab:
                station_df = df[df[station_col] == station_value]
                
                if not station_df.empty:
                    station_key = station_value.replace(' ', '_')
                    
                    # Check if modal is open
                    if f'modal_{station_key}' in st.session_state:
                        # Modal view
                        st.markdown(f'<div class="modal-header">{st.session_state[f"modal_{station_key}"]} <span class="modal-count">({len(st.session_state[f"modal_data_{station_key}"])} items)</span></div>', unsafe_allow_html=True)
                        
                        if st.button("← Back", key=f"close_{station_key}"):
                            del st.session_state[f'modal_{station_key}']
                            del st.session_state[f'modal_data_{station_key}']
                            st.rerun()
                        
                        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
                        
                        for idx, row in st.session_state[f'modal_data_{station_key}'].iterrows():
                            asset_number = row.get(df.columns[0], 'N/A')
                            
                            with st.expander(asset_number):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.markdown("**Type**")
                                    st.write(row.get(df.columns[2], "N/A"))
                                    st.markdown("**Quantity**")
                                    st.write(row.get(df.columns[4], "N/A"))
                                    
                                with col2:
                                    st.markdown("**Dimensions**")
                                    dims = f"{row.get(df.columns[5], 'N/A')} × {row.get(df.columns[6], 'N/A')} × {row.get(df.columns[7], 'N/A')} cm"
                                    st.write(dims)
                                    st.markdown("**Voltage**")
                                    st.write(row.get(df.columns[9], "N/A"))
                                    
                                with col3:
                                    st.markdown("**Power**")
                                    st.write(row.get(df.columns[10], "N/A"))
                                    st.markdown("**Status**")
                                    st.write(row.get(df.columns[11], "N/A"))
                    else:
                        # Card grid view with Type tabs and Asset Name filter
                        type_col = df.columns[2]  # Type column
                        
                        # Create tabs for type filtering
                        type_options = ['All', 'Tools', 'Equipment']
                        type_tabs = st.tabs(type_options)
                        
                        for type_tab, type_option in zip(type_tabs, type_options):
                            with type_tab:
                                # Filter by type
                                filtered = station_df.copy()
                                
                                if type_option != 'All':
                                    filtered = filtered[filtered[type_col].str.contains(type_option, case=False, na=False)]
                                
                                # Asset name filter dropdown
                                asset_names = ['All'] + sorted(filtered[asset_name_col].unique().tolist())
                                selected_asset = st.selectbox("Filter by Asset Name", options=asset_names, key=f"filter_{station_value}_{type_option}")
                                
                                # Apply asset name filter on already type-filtered data
                                if selected_asset != 'All':
                                    filtered = filtered[filtered[asset_name_col] == selected_asset]
                                
                                st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
                                
                                if not filtered.empty:
                                    grouped = filtered.groupby(asset_name_col)
                                    asset_groups = list(grouped)
                                    
                                    num_cols = 4
                                    for i in range(0, len(asset_groups), num_cols):
                                        cols = st.columns(num_cols)
                                        batch = asset_groups[i:i + num_cols]
                                        
                                        for col_idx, (asset_name, group_df) in enumerate(batch):
                                            with cols[col_idx]:
                                                count = len(group_df)
                                                safe_name = f"{station_key}_{type_option}_{i}_{col_idx}"
                                                
                                                # Create clickable card with invisible button
                                                button_id = f"btn_{safe_name}_{asset_name.replace(' ', '_')}"
                                                
                                                st.markdown(f"""
                                                <style>
                                                #{button_id} {{
                                                    position: absolute !important;
                                                    top: 0 !important;
                                                    left: 0 !important;
                                                    width: 100% !important;
                                                    height: 100% !important;
                                                    margin: -240px 0 220px 0 !important;
                                                    padding: 0 !important;
                                                    z-index: 10 !important;
                                                }}
                                                #{button_id} button {{
                                                    width: 100% !important;
                                                    height: 240px !important;
                                                    opacity: 0 !important;
                                                    cursor: pointer !important;
                                                    margin: 0 !important;
                                                    padding: 0 !important;
                                                    background: transparent !important;
                                                    border: none !important;
                                                    box-shadow: none !important;
                                                    color: transparent !important;
                                                    font-size: 0 !important;
                                                }}
                                                #{button_id} button:hover {{
                                                    background: transparent !important;
                                                    border: none !important;
                                                    box-shadow: none !important;
                                                    color: transparent !important;
                                                }}
                                                #{button_id} button:focus {{
                                                    background: transparent !important;
                                                    border: none !important;
                                                    box-shadow: none !important;
                                                    color: transparent !important;
                                                }}
                                                </style>
                                                <div class="asset-card">
                                                    <div class="asset-card-header">
                                                        <div class="asset-name">{asset_name}</div>
                                                    </div>
                                                    <div class="asset-card-body">
                                                        <div class="asset-count">{count} items</div>
                                                        <div class="asset-footer">View Details →</div>
                                                    </div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Invisible button overlay
                                                col_container = st.container()
                                                col_container.markdown(f'<div id="{button_id}"></div>', unsafe_allow_html=True)
                                                
                                                with col_container:
                                                    if st.button(" ", key=f"{safe_name}_{asset_name}"):
                                                        st.session_state[f'modal_{station_key}'] = asset_name
                                                        st.session_state[f'modal_data_{station_key}'] = group_df
                                                        st.rerun()
                                else:
                                    st.info("No assets found")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
