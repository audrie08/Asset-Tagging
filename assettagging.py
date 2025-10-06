import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

# Custom CSS for modern design without colors
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    
    .asset-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    
    .asset-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #999;
    }
    
    .asset-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .asset-number {
        background: #f5f5f5;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .asset-name {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .asset-type {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 12px;
    }
    
    .badge {
        display: inline-block;
        background: #f5f5f5;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-right: 8px;
    }
    
    .detail-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f5f5f5;
    }
    
    .detail-label {
        color: #666;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .detail-value {
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
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

def display_asset_card(row, columns):
    """Display individual asset as a card"""
    with st.container():
        st.markdown(f"""
        <div class="asset-card">
            <div class="asset-header">
                <span class="asset-number">{row.get(columns[0], 'N/A')}</span>
            </div>
            <div class="asset-name">{row.get(columns[3], 'Unknown Asset')}</div>
            <div class="asset-type">{row.get(columns[2], 'N/A')}</div>
            <div>
                <span class="badge">📦 Qty: {row.get(columns[4], '0')}</span>
                <span class="badge">{"✓ " + row.get(columns[11], 'Unknown') if columns[11] in row else 'Status Unknown'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 View Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f'<div class="detail-row"><span class="detail-label">Asset Number</span><span class="detail-value">{row.get(columns[0], "N/A")}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-row"><span class="detail-label">Station</span><span class="detail-value">{row.get(columns[1], "N/A")}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">{row.get(columns[2], "N/A")}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-row"><span class="detail-label">Asset Name</span><span class="detail-value">{row.get(columns[3], "N/A")}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-row"><span class="detail-label">Quantity</span><span class="detail-value">{row.get(columns[4], "N/A")}</span></div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="detail-row"><span class="detail-label">Length (cm)</span><span class="detail-value">{row.get(columns[5], "N/A")}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-row"><span class="detail-label">Width (cm)</span><span class="detail-value">{row.get(columns[6], "N/A")}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-row"><span class="detail-label">Height (cm)</span><span class="detail-value">{row.get(columns[7], "N/A")}</span></div>', unsafe_allow_html=True)
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
                        for idx, row in filtered.iterrows():
                            display_asset_card(row, df.columns)
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
