import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

# DEBUG MODE - Set to True to see debug info
DEBUG_MODE = True

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
    
    /* Debug styling */
    .debug-box {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 12px;
    }
    
    .debug-title {
        font-weight: bold;
        color: #856404;
        margin-bottom: 5px;
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
    
    /* Expander styling - Minimal with Yellow accent */
    .streamlit-expanderHeader {
        background: white !important;
        border: 1px solid #e8e8e8 !important;
        border-left: 3px solid #FFD700 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        margin-bottom: 12px !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #FFD700 !important;
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.15) !important;
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
    
    /* Modal header */
    .modal-header {
        font-size: 20px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #FFD700;
    }
    
    .modal-count {
        color: #999;
        font-weight: 400;
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

# DEBUG PANEL
if DEBUG_MODE:
    with st.expander("🐛 DEBUG PANEL - Session State", expanded=True):
        st.write("**All Session State Keys:**")
        modal_keys = {k: v for k, v in st.session_state.items() if 'modal' in k}
        if modal_keys:
            st.json(modal_keys)
        else:
            st.info("No modal keys in session state")

credentials = load_credentials()

if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)
    
    if not df.empty:
        df = df.drop(df.columns[0], axis=1)
        
        station_col = df.columns[1]
        asset_name_col = df.columns[3]
        
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
                    
                    # DEBUG: Show current station info
                    if DEBUG_MODE:
                        st.markdown(f"""
                        <div class="debug-box">
                            <div class="debug-title">📍 Current Station: {station_value}</div>
                            Station Key: {station_key}<br>
                            Modal Key: modal_{station_key}<br>
                            Modal Exists: {f'modal_{station_key}' in st.session_state}<br>
                            Modal Value: {st.session_state.get(f'modal_{station_key}', 'None')}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Check if modal is open for this station
                    modal_key = f'modal_{station_key}'
                    modal_data_key = f'modal_data_{station_key}'
                    
                    modal_exists = modal_key in st.session_state
                    modal_value = st.session_state.get(modal_key)
                    modal_active = modal_exists and modal_value is not None
                    
                    if DEBUG_MODE:
                        st.info(f"🔍 Modal Active Check: {modal_active} (exists: {modal_exists}, value: {modal_value})")
                    
                    if modal_active:
                        # MODAL VIEW - Asset Details
                        st.success("✅ MODAL VIEW MODE ACTIVE")
                        
                        st.markdown("---")
                        
                        # BIG VISIBLE BACK BUTTON
                        st.markdown("""
                        <div style="background: red; padding: 20px; margin: 20px 0;">
                            <h2 style="color: white; margin: 0;">🔴 BACK BUTTON SHOULD BE BELOW THIS 🔴</h2>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Define callback for back button
                        def close_modal():
                            if DEBUG_MODE:
                                st.toast("🔴 CALLBACK: Closing modal...")
                            if modal_key in st.session_state:
                                del st.session_state[modal_key]
                            if modal_data_key in st.session_state:
                                del st.session_state[modal_data_key]
                        
                        # Back button with callback
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            st.button(
                                "🔙 BACK TO ASSETS",
                                key=f"back_button_{station_key}",
                                type="primary",
                                on_click=close_modal,
                                use_container_width=True
                            )
                        
                        st.markdown("""
                        <div style="background: green; padding: 20px; margin: 20px 0;">
                            <h2 style="color: white; margin: 0;">🟢 BACK BUTTON SHOULD BE ABOVE THIS 🟢</h2>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        if DEBUG_MODE:
                            st.write(f"🔍 Modal still exists: {modal_key in st.session_state}")
                            st.write(f"🔍 Current modal value: {st.session_state.get(modal_key, 'DELETED')}")
                        
                        # Display modal header
                        asset_name_display = st.session_state.get(modal_key, 'Asset')
                        modal_data = st.session_state.get(modal_data_key, pd.DataFrame())
                        
                        if not modal_data.empty:
                            st.markdown(f'<div class="modal-header">{asset_name_display} <span class="modal-count">({len(modal_data)} items)</span></div>', unsafe_allow_html=True)
                            
                            st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
                            
                            # Display asset details in expanders
                            for idx, row in modal_data.iterrows():
                                asset_number = row.get(df.columns[0], 'N/A')
                                
                                with st.expander(asset_number, expanded=False):
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
                            st.error("⚠️ Modal data is empty!")
                            
                    else:
                        # CARD GRID VIEW - Asset Cards
                        st.info("📋 CARD GRID VIEW MODE ACTIVE")
                        
                        type_col = df.columns[2]
                        
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
                                                card_key = f"card_{station_key}_{type_option}_{i}_{col_idx}"
                                                
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
                                                
                                                # Invisible button overlay
                                                st.markdown("""
                                                <style>
                                                .element-container:has(> .stButton) {
                                                    position: relative;
                                                    margin-top: -200px;
                                                    margin-bottom: 110px;
                                                    z-index: 10;
                                                }
                                                .element-container:has(> .stButton) button {
                                                    width: 100%;
                                                    height: 200px;
                                                    opacity: 0;
                                                    cursor: pointer;
                                                    margin: 0 !important;
                                                    padding: 0;
                                                    background: transparent !important;
                                                    border: none !important;
                                                }
                                                </style>
                                                """, unsafe_allow_html=True)
                                                
                                                # Card click handler with callback
                                                def open_modal():
                                                    st.session_state[modal_key] = asset_name
                                                    st.session_state[modal_data_key] = group_df.copy()
                                                    if DEBUG_MODE:
                                                        st.toast(f"✅ Opening modal: {asset_name}")
                                                
                                                st.button(
                                                    " ", 
                                                    key=card_key, 
                                                    on_click=open_modal,
                                                    use_container_width=True
                                                )
                                else:
                                    st.info("No assets found")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
