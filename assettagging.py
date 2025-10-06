import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
        background: #fafafa;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    h1 {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    
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
    
    [data-testid="column"] {
        padding: 0 6px;
    }
    
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

def create_asset_card_html(asset_name, count, asset_codes, key):
    """Create HTML for asset card"""
    preview_codes = asset_codes[:2] if len(asset_codes) > 2 else asset_codes
    preview_html = "".join([f'<div class="asset-tag">{code}</div>' for code in preview_codes])
    if len(asset_codes) > 2:
        preview_html += f'<div class="asset-tag">+{len(asset_codes) - 2} more</div>'
    
    return f"""
    <div class="asset-card" onclick="parent.postMessage({{type: 'streamlit:setComponentValue', key: '{key}', value: '{asset_name}'}}, '*')">
        <div class="asset-name">{asset_name}</div>
        <div class="asset-count">{count} items</div>
        <div class="asset-preview">
            {preview_html}
        </div>
    </div>
    """

def render_asset_cards_grid(grouped_df, asset_name_col, df_columns, station_key):
    """Render asset cards in grid layout"""
    asset_card_style = """
    <style>
        .asset-card {
            background: white;
            border: 2px solid #e5e5e5;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 16px;
        }
        .asset-card:hover {
            border-color: #333;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }
        .asset-name {
            font-weight: 600;
            font-size: 15px;
            color: #1a1a1a;
            margin-bottom: 8px;
        }
        .asset-count {
            background: #f5f5f5;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            color: #666;
            display: inline-block;
            margin-bottom: 8px;
        }
        .asset-preview {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 8px;
        }
        .asset-tag {
            background: #f5f5f5;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            color: #666;
        }
    </style>
    """
    
    grouped = grouped_df.groupby(asset_name_col)
    asset_groups = list(grouped)
    
    num_cols = 5
    for i in range(0, len(asset_groups), num_cols):
        cols = st.columns(num_cols)
        batch = asset_groups[i:i + num_cols]
        
        for col_idx, (asset_name, group_df) in enumerate(batch):
            with cols[col_idx]:
                asset_codes = group_df[df_columns[0]].tolist()
                card_key = f"{station_key}_{asset_name.replace(' ', '_')}"
                
                # Create clickable card
                if st.button(f"📦 {asset_name}", key=card_key, use_container_width=True):
                    st.session_state[f'modal_{station_key}'] = asset_name
                    st.session_state[f'modal_data_{station_key}'] = group_df
                
                # Show preview info
                st.caption(f"{len(group_df)} items")

def render_modal(asset_name, group_df, df_columns, station_key):
    """Render modal with asset details"""
    st.markdown(f"### {asset_name} ({len(group_df)} items)")
    
    if st.button("✕ Close", key=f"close_{station_key}"):
        if f'modal_{station_key}' in st.session_state:
            del st.session_state[f'modal_{station_key}']
        if f'modal_data_{station_key}' in st.session_state:
            del st.session_state[f'modal_data_{station_key}']
        st.rerun()
    
    st.markdown("---")
    
    # Display each asset with expander
    for idx, row in group_df.iterrows():
        asset_number = row.get(df_columns[0], 'N/A')
        
        with st.expander(f"🔖 {asset_number}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**TYPE**")
                st.write(row.get(df_columns[2], "N/A"))
                st.markdown(f"**QUANTITY**")
                st.write(row.get(df_columns[4], "N/A"))
                
            with col2:
                st.markdown(f"**DIMENSIONS**")
                dims = f"{row.get(df_columns[5], 'N/A')} × {row.get(df_columns[6], 'N/A')} × {row.get(df_columns[7], 'N/A')} cm"
                st.write(dims)
                st.markdown(f"**VOLTAGE**")
                st.write(row.get(df_columns[9], "N/A"))
                
            with col3:
                st.markdown(f"**POWER**")
                st.write(row.get(df_columns[10], "N/A"))
                st.markdown(f"**STATUS**")
                status = row.get(df_columns[11], "N/A")
                if "Working" in status:
                    st.success(status)
                else:
                    st.error(status)

# Main App
st.title("🏷️ Asset Tagging System")
st.markdown("Manage and track all commissary assets")

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
        
        st.markdown("---")
        
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
                        # Show modal
                        render_modal(
                            st.session_state[f'modal_{station_key}'],
                            st.session_state[f'modal_data_{station_key}'],
                            df.columns,
                            station_key
                        )
                    else:
                        # Show card grid
                        col_search, col_filter = st.columns([2, 1])
                        
                        with col_search:
                            search_term = st.text_input("🔍 Search assets", placeholder="Type to search...", key=f"search_{station_value}")
                        
                        with col_filter:
                            asset_names = ['All'] + sorted(station_df[asset_name_col].unique().tolist())
                            selected_asset = st.selectbox("Filter by Asset Name", options=asset_names, key=f"filter_{station_value}")
                        
                        filtered = station_df.copy()
                        
                        if selected_asset != 'All':
                            filtered = filtered[filtered[asset_name_col] == selected_asset]
                        
                        if search_term:
                            mask = filtered[asset_name_col].str.contains(search_term, case=False, na=False)
                            filtered = filtered[mask]
                        
                        st.caption(f"Showing {len(filtered)} of {len(station_df)} assets")
                        
                        if not filtered.empty:
                            render_asset_cards_grid(filtered, asset_name_col, df.columns, station_key)
                        else:
                            st.info("No assets found matching your filters.")
                    
                    # Download button
                    st.markdown("---")
                    csv = station_df.to_csv(index=False)
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
