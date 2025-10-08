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
        color: #999;
        margin-bottom: 2rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 0 20px;
        font-weight: 500;
        font-size: 14px;
        color: #666;
        border: none;
        background: transparent;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1a1a1a;
    }
    .stTabs [aria-selected="true"] {
        color: #1a1a1a;
        border-bottom-color: #1a1a1a;
        background: transparent;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid #f0f0f0;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
        color: #1a1a1a;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px;
        font-weight: 500;
        color: #666;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        padding: 10px 14px;
        font-size: 14px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #999;
        box-shadow: none;
    }
    .stSelectbox > div > div {
        border-radius: 6px;
        border: 1px solid #e0e0e0;
    }
    
    /* Buttons */
    .stButton > button {
        background: transparent !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        text-align: center !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #666 !important;
        transition: all 0.2s ease !important;
        height: auto !important;
        margin-top: 8px !important;
    }
    .stButton > button:hover {
        background: #fafafa !important;
        border-color: #999 !important;
        color: #1a1a1a !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: white !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        margin-bottom: 12px !important;
        margin-top: 50px !important;

    }
    
    .streamlit-expanderHeader:hover {
        border-color: #999 !important;
    }
    [data-testid="stExpander"] {
        border: none !important;
    }
    .streamlit-expanderContent {
        background: #fafafa !important;
        border: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 18px !important;
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

def get_avatar_color(name):
    """Generate consistent color for avatar based on name"""
    colors = [
        "#8B5CF6", "#6366F1", "#3B82F6", "#06B6D4", 
        "#10B981", "#F59E0B", "#EF4444", "#EC4899"
    ]
    index = sum(ord(c) for c in name) % len(colors)
    return colors[index]

# Main App
st.markdown('<div class="header-title">Asset Tagging</div>', unsafe_allow_html=True)
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
                        st.markdown(f'<div style="font-size: 20px; font-weight: 600; color: #1a1a1a; margin-bottom: 1rem;">{st.session_state[f"modal_{station_key}"]} <span style="color: #999; font-weight: 400;">({len(st.session_state[f"modal_data_{station_key}"])} items)</span></div>', unsafe_allow_html=True)
                        
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
                                                
                                                # Create clickable metric-style card with CSS hover
                                                st.markdown(f"""
                                                <style>
                                                .card-{safe_name} {{
                                                    background: white;
                                                    border: 1px solid #f0f0f0;
                                                    border-radius: 20px;
                                                    padding: 1.5rem 1.25rem;
                                                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                                                    transition: all 0.3s ease;
                                                    min-height: 130px;
                                                    display: flex;
                                                    flex-direction: column;
                                                    justify-content: space-between;
                                                    margin-bottom: 90px;
                                                }}
                                                .card-{safe_name}:hover {{
                                                    box-shadow: 0 12px 24px rgba(0,0,0,0.15);
                                                    transform: translateY(-6px);
                                                    border-color: #ccc;
                                                }}
                                                </style>
                                                <div class="card-{safe_name}">
                                                    <div>
                                                        <div style="font-size: 18px; font-weight: 600; color: #1a1a1a; line-height: 1.3; margin-bottom: 8px;">
                                                            {asset_name}
                                                        </div>
                                                        <div style="font-size: 13px; font-weight: 500; color: #999; line-height: 1.4;">
                                                            {count} items
                                                        </div>
                                                    </div>
                                                    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #f5f5f5; font-size: 13px; font-weight: 500; color: #666;">
                                                        View Details →
                                                    </div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Button positioned over the card
                                                st.markdown("""
                                                <style>
                                                .element-container:has(> .stButton) {
                                                    position: relative;
                                                    margin-top: -170px;
                                                    margin-bottom: 90px;
                                                    z-index: 10;
                                                }
                                                .element-container:has(> .stButton) button {
                                                    width: 100%;
                                                    height: 150px;
                                                    opacity: 0;
                                                    cursor: pointer;
                                                    margin: 0;
                                                    padding: 0;
                                                }
                                                </style>
                                                """, unsafe_allow_html=True)
                                                
                                                if st.button("c", key=f"{safe_name}_{asset_name}", use_container_width=True):
                                                    st.session_state[f'modal_{station_key}'] = asset_name
                                                    st.session_state[f'modal_data_{station_key}'] = group_df
                                                    st.rerun()
                                else:
                                    st.info("No assets found")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
