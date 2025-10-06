import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

# Hide default Streamlit elements
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    [data-testid="column"] {padding: 0 6px;}
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

def generate_asset_cards_html(grouped_df, asset_name_col, df_columns):
    """Generate custom HTML for asset cards"""
    grouped = grouped_df.groupby(asset_name_col)
    
    cards_html = ""
    for asset_name, group_df in grouped:
        count = len(group_df)
        asset_codes = group_df[df_columns[0]].tolist()[:3]
        
        cards_html += f"""
        <div class="asset-card">
            <div class="asset-card-header">
                <div class="asset-name">{asset_name}</div>
                <div class="asset-count">{count} items</div>
            </div>
        </div>
        """
    
    full_html = f"""
    <style>
        .asset-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-top: 20px;
        }}
        
        .asset-card {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .asset-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}
        
        .asset-card:hover {{
            border-color: #667eea;
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(102, 126, 234, 0.15);
        }}
        
        .asset-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .asset-card-header {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .asset-name {{
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
            letter-spacing: -0.01em;
        }}
        
        .asset-count {{
            font-size: 13px;
            color: #666;
            font-weight: 500;
        }}
        
        @media (max-width: 1400px) {{
            .asset-grid {{
                grid-template-columns: repeat(4, 1fr);
            }}
        }}
        
        @media (max-width: 1000px) {{
            .asset-grid {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
    </style>
    
    <div class="asset-grid">
        {cards_html}
    </div>
    """
    
    return full_html

# Main App
st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="font-size: 32px; font-weight: 700; color: #1a1a1a; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
        Asset Tagging System
    </h1>
    <p style="color: #666; font-size: 16px; margin: 0;">
        Manage and track all commissary assets
    </p>
</div>
""", unsafe_allow_html=True)

credentials = load_credentials()

if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)
    
    if not df.empty:
        df = df.drop(df.columns[0], axis=1)
        
        station_col = df.columns[1]
        asset_name_col = df.columns[3]
        
        # Statistics with custom styling
        st.markdown("""
        <style>
            [data-testid="stMetric"] {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                border: 2px solid #f0f0f0;
                transition: all 0.3s ease;
            }
            [data-testid="stMetric"]:hover {
                border-color: #667eea;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
            }
            [data-testid="stMetricValue"] {
                font-size: 36px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            [data-testid="stMetricLabel"] {
                font-size: 14px;
                font-weight: 600;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Assets", len(df))
        with col2:
            working_count = len(df[df[df.columns[11]].str.contains("Working", case=False, na=False)])
            st.metric("Working", working_count)
        with col3:
            not_working = len(df[df[df.columns[11]].str.contains("Not Working", case=False, na=False)])
            st.metric("Not Working", not_working)
        
        st.markdown("<div style='margin: 2rem 0; height: 1px; background: #e0e0e0;'></div>", unsafe_allow_html=True)
        
        # Custom tabs styling
        st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: white;
                padding: 8px;
                border-radius: 12px;
                border: 2px solid #f0f0f0;
            }
            .stTabs [data-baseweb="tab"] {
                height: 48px;
                border-radius: 8px;
                padding: 0 24px;
                font-weight: 600;
                font-size: 14px;
                border: none;
                color: #666;
                transition: all 0.2s ease;
            }
            .stTabs [data-baseweb="tab"]:hover {
                background: #f5f5f5;
                color: #1a1a1a;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white !important;
            }
            
            /* Input styling */
            .stTextInput > div > div > input {
                border-radius: 10px;
                border: 2px solid #e0e0e0;
                padding: 12px 16px;
                font-size: 14px;
                transition: all 0.2s ease;
            }
            .stTextInput > div > div > input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .stSelectbox > div > div {
                border-radius: 10px;
                border: 2px solid #e0e0e0;
            }
            
            /* Download button */
            .stDownloadButton > button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 600;
                border: none;
                transition: all 0.3s ease;
            }
            .stDownloadButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
        </style>
        """, unsafe_allow_html=True)
        
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
                        st.markdown(f"""
                        <div style="margin-bottom: 2rem;">
                            <h2 style="font-size: 24px; font-weight: 700; color: #1a1a1a; margin-bottom: 0.5rem;">
                                {st.session_state[f'modal_{station_key}']} 
                                <span style="color: #666; font-weight: 500;">
                                    ({len(st.session_state[f'modal_data_{station_key}'])} items)
                                </span>
                            </h2>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("← Back to Assets", key=f"close_{station_key}"):
                            del st.session_state[f'modal_{station_key}']
                            del st.session_state[f'modal_data_{station_key}']
                            st.rerun()
                        
                        st.markdown("<div style='margin: 1.5rem 0; height: 1px; background: #e0e0e0;'></div>", unsafe_allow_html=True)
                        
                        # Display asset items with improved styling
                        st.markdown("""
                        <style>
                            .streamlit-expanderHeader {
                                background: white !important;
                                border: 2px solid #e0e0e0 !important;
                                border-radius: 10px !important;
                                padding: 16px 20px !important;
                                font-weight: 600 !important;
                                font-size: 14px !important;
                                transition: all 0.2s ease !important;
                                margin-bottom: 12px !important;
                            }
                            .streamlit-expanderHeader:hover {
                                border-color: #667eea !important;
                                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1) !important;
                            }
                            [data-testid="stExpander"] {
                                border: none !important;
                            }
                            .streamlit-expanderContent {
                                background: #fafafa !important;
                                border: none !important;
                                border-radius: 0 0 10px 10px !important;
                                padding: 20px !important;
                            }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        for idx, row in st.session_state[f'modal_data_{station_key}'].iterrows():
                            asset_number = row.get(df.columns[0], 'N/A')
                            
                            with st.expander(f"{asset_number}"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.markdown("**TYPE**")
                                    st.write(row.get(df.columns[2], "N/A"))
                                    st.markdown("**QUANTITY**")
                                    st.write(row.get(df.columns[4], "N/A"))
                                    
                                with col2:
                                    st.markdown("**DIMENSIONS**")
                                    dims = f"{row.get(df.columns[5], 'N/A')} × {row.get(df.columns[6], 'N/A')} × {row.get(df.columns[7], 'N/A')} cm"
                                    st.write(dims)
                                    st.markdown("**VOLTAGE**")
                                    st.write(row.get(df.columns[9], "N/A"))
                                    
                                with col3:
                                    st.markdown("**POWER**")
                                    st.write(row.get(df.columns[10], "N/A"))
                                    st.markdown("**STATUS**")
                                    status = row.get(df.columns[11], "N/A")
                                    if "Working" in status:
                                        st.success(status)
                                    else:
                                        st.error(status)
                    else:
                        # Card grid view
                        col_search, col_filter = st.columns([2, 1])
                        
                        with col_search:
                            search_term = st.text_input("Search assets", placeholder="Type to search...", key=f"search_{station_value}", label_visibility="collapsed")
                        
                        with col_filter:
                            asset_names = ['All'] + sorted(station_df[asset_name_col].unique().tolist())
                            selected_asset = st.selectbox("Filter", options=asset_names, key=f"filter_{station_value}", label_visibility="collapsed")
                        
                        filtered = station_df.copy()
                        
                        if selected_asset != 'All':
                            filtered = filtered[filtered[asset_name_col] == selected_asset]
                        
                        if search_term:
                            mask = filtered[asset_name_col].str.contains(search_term, case=False, na=False)
                            filtered = filtered[mask]
                        
                        st.markdown(f"<p style='color: #666; font-size: 14px; margin: 1rem 0;'>Showing {len(filtered)} of {len(station_df)} assets</p>", unsafe_allow_html=True)
                        
                        if not filtered.empty:
                            # Display as clickable cards using custom HTML and buttons
                            grouped = filtered.groupby(asset_name_col)
                            asset_groups = list(grouped)
                            
                            num_cols = 5
                            for i in range(0, len(asset_groups), num_cols):
                                cols = st.columns(num_cols)
                                batch = asset_groups[i:i + num_cols]
                                
                                for col_idx, (asset_name, group_df) in enumerate(batch):
                                    with cols[col_idx]:
                                        # Custom styled button
                                        if st.button(
                                            f"{asset_name}\n\n{len(group_df)} items",
                                            key=f"{station_key}_{asset_name}",
                                            use_container_width=True
                                        ):
                                            st.session_state[f'modal_{station_key}'] = asset_name
                                            st.session_state[f'modal_data_{station_key}'] = group_df
                                            st.rerun()
                        else:
                            st.info("No assets found matching your filters.")
                    
                    # Download button
                    st.markdown("<div style='margin: 2rem 0; height: 1px; background: #e0e0e0;'></div>", unsafe_allow_html=True)
                    csv = station_df.to_csv(index=False)
                    st.download_button(
                        label=f"Download {tab_name} Data",
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
