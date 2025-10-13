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
    .block-container {padding: 2rem 3rem;}
    [data-testid="column"] {padding: 0 8px;}
    
    /* Header styling */
    .header-title {
        font-size: 28px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.25rem;
    }
    .header-subtitle {
        font-size: 14px;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Tabs - Gray background with Yellow active */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #f5f5f5;
        padding: 0.5rem;
        border-radius: 10px;
        border: none;
        margin-bottom: 2rem;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 0 20px;
        font-weight: 500;
        font-size: 14px;
        color: #666;
        border: none;
        background: transparent;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1a1a1a;
        background: #918e83;
    }
    .stTabs [aria-selected="true"] {
        color: #FFD700;
        background: #1a1a1a;
        font-weight: 600;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 10px 14px;
        font-size: 14px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FFD700;
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.1);
    }
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .stSelectbox > div > div:hover {
        border-color: #FFD700;
    }
    
    /* Buttons - Yellow accent */
    .stButton > button {
        background: white !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 10px 18px !important;
        text-align: center !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #1a1a1a !important;
        transition: all 0.2s ease !important;
        height: auto !important;
        margin-top: 8px !important;
    }
    .stButton > button:hover {
        background: #FFD700 !important;
        border-color: #FFD700 !important;
        color: #1a1a1a !important;
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3) !important;
    }
    
    /* Card styling - Colorful with Yellow/Gray variations */
    .asset-card {
        background: white;
        border: 2px solid #999;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
        min-height: 150px;
        margin-bottom: 1.5rem;
    }
    
    .asset-card:hover {
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        transform: translateY(-4px);
    }
    
    .asset-card-header {
        padding: 1rem 1.25rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
    }
    
    .asset-card-body {
        padding: 1.25rem;
        background: white;
    }
    
    .card-dark .asset-card-header {
        background: linear-gradient(135deg, #4a4a4a 0%, #2d2d2d 100%);
    }
    
    .asset-name {
        font-size: 18px;
        font-weight: 600;
        color: white;
        line-height: 1.3;
        margin: 0;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .asset-count {
        font-size: 13px;
        font-weight: 500;
        color: #666;
        line-height: 1.4;
        margin-bottom: 1rem;
    }
    
    .asset-footer {
        padding-top: 1rem;
        border-top: 1px solid #f5f5f5;
        font-size: 13px;
        font-weight: 500;
        color: #999;
        transition: color 0.2s ease;
    }
    
    .asset-card:hover .asset-footer {
        color: #FFD700;
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

credentials = load_credentials()

if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)
    
    if not df.empty:
        df = df.drop(df.columns[0], axis=1)
        
        station_col = df.columns[1]
        asset_name_col = df.columns[3]
        type_col = df.columns[2]
        
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
                    # Type filtering tabs
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
                            selected_asset = st.selectbox(
                                "Filter by Asset Name", 
                                options=asset_names, 
                                key=f"filter_{station_value}_{type_option}"
                            )
                            
                            # Apply asset name filter
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
                                            
                                            # Create card
                                            st.markdown(f"""
                                            <div class="asset-card card-dark">
                                                <div class="asset-card-header">
                                                    <div class="asset-name">{asset_name}</div>
                                                </div>
                                                <div class="asset-card-body">
                                                    <div class="asset-count">{count} items</div>
                                                    <div class="asset-footer">View Details →</div>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                            else:
                                st.info("No assets found")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
