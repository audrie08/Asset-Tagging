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
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }
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
    
    /* Metrics - White with Colored accents */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e8e8e8;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
    }
    [data-testid="stMetric"]:nth-child(1)::before {
        background: linear-gradient(90deg, #FFD700, #FFC107);
    }
    [data-testid="stMetric"]:nth-child(2)::before {
        background: linear-gradient(90deg, #9e9e9e, #757575);
    }
    [data-testid="stMetric"]:nth-child(3)::before {
        background: linear-gradient(90deg, #4a4a4a, #2d2d2d);
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
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
        background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%) !important;
        border: 1px solid #e8e8e8 !important;
        border-left: 4px solid #FFD700 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        margin-bottom: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02) !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-left-color: #FFC107 !important;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.15) !important;
        transform: translateX(4px);
    }
    [data-testid="stExpander"] {
        border: none !important;
        margin-bottom: 1rem !important;
    }
    .streamlit-expanderContent {
        background: white !important;
        border: 1px solid #e8e8e8 !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 0 !important;
        margin-top: -8px !important;
    }
    
    /* Modern Info Grid Styling */
    .info-section {
        padding: 1.5rem;
        background: #fafafa;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .info-row {
        display: grid;
        grid-template-columns: 140px 1fr;
        gap: 1rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #e8e8e8;
        align-items: start;
    }
    
    .info-row:last-child {
        border-bottom: none;
    }
    
    .info-label {
        font-size: 12px;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding-top: 2px;
    }
    
    .info-value {
        font-size: 14px;
        font-weight: 500;
        color: #1a1a1a;
        line-height: 1.5;
    }
    
    .image-section {
        padding: 1.5rem;
        background: white;
    }
    
    .image-wrapper {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e8e8e8;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    /* Modern Detail Card Styling */
    .detail-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e8e8e8;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    
    .detail-card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }
    
    .detail-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f5f5f5;
        margin-bottom: 1.5rem;
    }
    
    .detail-asset-number {
        font-size: 20px;
        font-weight: 600;
        color: #1a1a1a;
        flex: 1;
    }
    
    .detail-badge {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        background: #FFD700;
        color: #1a1a1a;
    }
    
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
    }
    
    .detail-item {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .detail-label {
        font-size: 12px;
        font-weight: 600;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .detail-value {
        font-size: 15px;
        font-weight: 500;
        color: #1a1a1a;
        line-height: 1.4;
    }
    
    .detail-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e8e8e8, transparent);
        margin: 1.5rem 0;
    }
    
    .image-container {
        background: #f8f8f8;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 2px dashed #e0e0e0;
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .image-placeholder {
        color: #999;
        font-size: 14px;
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
    
    /* Color variations for cards */
    .card-yellow .asset-card-header {
        background: linear-gradient(135deg, #FFD700 0%, #FFC107 100%);
    }
    
    .card-dark .asset-card-header {
        background: linear-gradient(135deg, #4a4a4a 0%, #2d2d2d 100%);
    }
    
    .card-gray .asset-card-header {
        background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
    }
    
    .card-amber .asset-card-header {
        background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%);
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

def convert_google_drive_url(url):
    """Convert Google Drive sharing URL to direct image URL"""
    if not url or url.strip() == "" or url == "N/A":
        return None
    
    # Check if it's a Google Drive URL
    if "drive.google.com" in url:
        # Extract file ID from the URL
        if "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
            # Use thumbnail URL which works better with Streamlit
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    
    return url

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
                    
                    # --- Handle query params for modal persistence ---
                    query_params = st.query_params
                    
                    # If modal info is saved in query params, restore it into session_state
                    if f'modal_{station_key}' not in st.session_state:
                        if query_params.get("station") == station_key and "asset" in query_params:
                            asset_name = query_params["asset"]
                            # Rebuild modal state from URL
                            filtered_data = df[(df[station_col] == station_value) & (df[asset_name_col] == asset_name)]
                            if not filtered_data.empty:
                                st.session_state[f'modal_{station_key}'] = asset_name
                                st.session_state[f'modal_data_{station_key}'] = filtered_data
                    
                    # Check if modal is open
                    if f'modal_{station_key}' in st.session_state:
                        # Modal view
                        st.markdown(f'<div class="modal-header">{st.session_state[f"modal_{station_key}"]} <span class="modal-count">({len(st.session_state[f"modal_data_{station_key}"])} items)</span></div>', unsafe_allow_html=True)
                        
                        if st.button("← Back", key=f"close_{station_key}"):
                            del st.session_state[f'modal_{station_key}']
                            del st.session_state[f'modal_data_{station_key}']
                            # Remove modal info from URL
                            st.query_params.clear()
                            st.rerun()
                        
                        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
                        
                        for idx, row in st.session_state[f'modal_data_{station_key}'].iterrows():
                            asset_number = row.get(df.columns[0], 'N/A')
                            
                            with st.expander(asset_number):
                                # Create two main columns: info (70%) and image (30%)
                                info_col, image_col = st.columns([7, 3])
                                
                                with info_col:
                                    st.markdown("""
                                    <div class="info-section">
                                    """, unsafe_allow_html=True)
                                    
                                    # Row 1: Type and Quantity
                                    st.markdown(f"""
                                    <div class="info-row">
                                        <div class="info-label">Type</div>
                                        <div class="info-value">{row.get(df.columns[2], "N/A")}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown(f"""
                                    <div class="info-row">
                                        <div class="info-label">Quantity</div>
                                        <div class="info-value">{row.get(df.columns[4], "N/A")}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Row 2: Dimensions
                                    dims = f"{row.get(df.columns[5], 'N/A')} × {row.get(df.columns[6], 'N/A')} × {row.get(df.columns[7], 'N/A')} cm"
                                    st.markdown(f"""
                                    <div class="info-row">
                                        <div class="info-label">Dimensions</div>
                                        <div class="info-value">{dims}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Row 3: Voltage
                                    st.markdown(f"""
                                    <div class="info-row">
                                        <div class="info-label">Voltage</div>
                                        <div class="info-value">{row.get(df.columns[10], "N/A")}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Row 4: Power
                                    st.markdown(f"""
                                    <div class="info-row">
                                        <div class="info-label">Power</div>
                                        <div class="info-value">{row.get(df.columns[11], "N/A")}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Row 5: Status
                                    st.markdown(f"""
                                    <div class="info-row">
                                        <div class="info-label">Status</div>
                                        <div class="info-value">{row.get(df.columns[12], "N/A")}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown("</div>", unsafe_allow_html=True)
                                
                                with image_col:
                                    st.markdown('<div class="image-section">', unsafe_allow_html=True)
                                    st.markdown('<div class="info-label" style="margin-bottom: 0.75rem;">IMAGE</div>', unsafe_allow_html=True)
                                    
                                    image_url = row.get(df.columns[9], "")
                                    
                                    # DEBUG INFO
                                    with st.expander("🔍 Debug Info", expanded=False):
                                        st.write(f"**Column Index:** {9}")
                                        st.write(f"**Column Name:** {df.columns[9]}")
                                        st.write(f"**Original URL:** `{image_url}`")
                                        st.write(f"**URL Length:** {len(str(image_url))}")
                                        st.write(f"**URL Type:** {type(image_url)}")
                                        converted_url = convert_google_drive_url(image_url)
                                        st.write(f"**Converted URL:** `{converted_url}`")
                                        st.write(f"**Is Google Drive URL:** {'drive.google.com' in str(image_url)}")
                                        st.markdown(f"**Test URL:** [Click to test]({converted_url})")
                                        st.info("⚠️ If image doesn't load, the file may not be publicly shared. Go to Google Drive > Share > Change to 'Anyone with the link' > Viewer permission")
                                    
                                    converted_url = convert_google_drive_url(image_url)
                                    
                                    if converted_url:
                                        st.markdown('<div class="image-wrapper">', unsafe_allow_html=True)
                                        try:
                                            st.image(converted_url, use_container_width=True)
                                        except Exception as e:
                                            st.error(f"Image load error: {str(e)}")
                                            st.markdown(f"""
                                            <div style='padding: 1rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #FFD700;'>
                                                <p style='color: #856404; margin-bottom: 0.5rem; font-weight: 500;'>⚠️ Image cannot be displayed</p>
                                                <p style='color: #856404; font-size: 13px; margin-bottom: 0.5rem;'>Make sure the file is publicly shared in Google Drive</p>
                                                <a href='{image_url}' target='_blank' style='color: #FFD700; text-decoration: none; font-weight: 500;'>View Image in Google Drive →</a>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    else:
                                        st.markdown('<div style="padding: 2rem; background: #f8f8f8; border-radius: 8px; text-align: center; color: #999;">No image available</div>', unsafe_allow_html=True)
                                    
                                    st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        # Card grid view with Type tabs and Asset Name filter
                        type_col = df.columns[2]  # Type column
                        
                        # Create tabs for type filtering (removed 'All' option)
                        type_options = ['Tools', 'Equipment']
                        type_tabs = st.tabs(type_options)
                        
                        for type_tab, type_option in zip(type_tabs, type_options):
                            with type_tab:
                                # Filter by type
                                filtered = station_df[station_df[type_col].str.contains(type_option, case=False, na=False)]
                                
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
                                                
                                                # All cards use dark/black color
                                                card_color = 'card-dark'
                                                
                                                # Create clickable card with black header
                                                st.markdown(f"""
                                                <div class="asset-card {card_color}">
                                                    <div class="asset-card-header">
                                                        <div class="asset-name">{asset_name}</div>
                                                    </div>
                                                    <div class="asset-card-body">
                                                        <div class="asset-count">{count} items</div>
                                                        <div class="asset-footer">View Details →</div>
                                                    </div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Button positioned over the card
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
                                                    margin: 0;
                                                    padding: 0;
                                                    background: transparent !important;
                                                    border: none !important;
                                                }
                                                </style>
                                                """, unsafe_allow_html=True)
                                                
                                                if st.button(" ", key=f"{safe_name}_{asset_name}", use_container_width=True):
                                                    st.session_state[f'modal_{station_key}'] = asset_name
                                                    st.session_state[f'modal_data_{station_key}'] = group_df
                                                    st.query_params["station"] = station_key
                                                    st.query_params["asset"] = asset_name
                                                    st.rerun()
                                else:
                                    st.info("No assets found")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
