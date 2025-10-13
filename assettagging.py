import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Asset Tagging", layout="wide")

# ---------------- STYLES ----------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding: 2rem 3rem;}
[data-testid="column"] {padding: 0 8px;}

.header-title {font-size: 28px; font-weight: 600; color: #1a1a1a; margin-bottom: 0.25rem;}
.header-subtitle {font-size: 14px; color: #666; margin-bottom: 2rem;}

.stTabs [data-baseweb="tab-list"] {gap: 0.5rem; background: #f5f5f5; padding: 0.5rem; border-radius: 10px; border: none; margin-bottom: 2rem; justify-content: center;}
.stTabs [data-baseweb="tab"] {height: 48px; padding: 0 20px; font-weight: 500; font-size: 14px; color: #666; border: none; background: transparent; border-radius: 8px;}
.stTabs [data-baseweb="tab"]:hover {color: #1a1a1a; background: #918e83;}
.stTabs [aria-selected="true"] {color: #FFD700; background: #1a1a1a; font-weight: 600;}

[data-testid="stMetric"] {background: white; padding: 1.5rem; border-radius: 10px; border: 1px solid #e8e8e8; position: relative; overflow: hidden; transition: all 0.2s ease;}
[data-testid="stMetric"]::before {content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px;}
[data-testid="stMetric"]:nth-child(1)::before {background: linear-gradient(90deg, #FFD700, #FFC107);}
[data-testid="stMetric"]:nth-child(2)::before {background: linear-gradient(90deg, #9e9e9e, #757575);}
[data-testid="stMetric"]:nth-child(3)::before {background: linear-gradient(90deg, #4a4a4a, #2d2d2d);}
[data-testid="stMetric"]:hover {transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);}
[data-testid="stMetricValue"] {font-size: 28px; font-weight: 600; color: #1a1a1a;}
[data-testid="stMetricLabel"] {font-size: 13px; font-weight: 500; color: #666;}

.stTextInput > div > div > input {border-radius: 8px; border: 1px solid #e0e0e0; padding: 10px 14px; font-size: 14px;}
.stTextInput > div > div > input:focus {border-color: #FFD700; box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.1);}
.stSelectbox > div > div {border-radius: 8px; border: 1px solid #e0e0e0;}
.stSelectbox > div > div:hover {border-color: #FFD700;}

.stButton > button {background: white !important; border: 1px solid #e0e0e0 !important; border-radius: 8px !important; padding: 10px 18px !important; font-size: 13px !important; font-weight: 500 !important; color: #1a1a1a !important; transition: all 0.2s ease !important; height: auto !important; margin-top: 8px !important;}
.stButton > button:hover {background: #FFD700 !important; border-color: #FFD700 !important; color: #1a1a1a !important; box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3) !important;}

.streamlit-expanderHeader {background: white !important; border: 1px solid #e8e8e8 !important; border-left: 3px solid #FFD700 !important; border-radius: 8px !important; padding: 14px 18px !important; font-weight: 500 !important; font-size: 14px !important; margin-bottom: 12px !important; transition: all 0.2s ease !important;}
.streamlit-expanderHeader:hover {border-color: #FFD700 !important; box-shadow: 0 2px 8px rgba(255, 215, 0, 0.15) !important;}
[data-testid="stExpander"] {border: none !important;}
.streamlit-expanderContent {background: #fafafa !important; border: none !important; border-radius: 0 0 8px 8px !important; padding: 18px !important;}

.asset-card {background: white; border: 2px solid #999; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04); transition: all 0.3s ease; min-height: 150px; margin-bottom: 1.5rem;}
.asset-card:hover {box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1); transform: translateY(-4px);}
.asset-card-header {padding: 1rem 1.25rem; border-bottom: 2px solid rgba(255, 255, 255, 0.3);}
.asset-card-body {padding: 1.25rem; background: white;}
.card-yellow .asset-card-header {background: linear-gradient(135deg, #FFD700 0%, #FFC107 100%);}
.card-dark .asset-card-header {background: linear-gradient(135deg, #4a4a4a 0%, #2d2d2d 100%);}
.card-gray .asset-card-header {background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);}
.card-amber .asset-card-header {background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%);}
.asset-name {font-size: 18px; font-weight: 600; color: white; line-height: 1.3; margin: 0; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);}
.asset-count {font-size: 13px; font-weight: 500; color: #666; line-height: 1.4; margin-bottom: 1rem;}
.asset-footer {padding-top: 1rem; border-top: 1px solid #f5f5f5; font-size: 13px; font-weight: 500; color: #999; transition: color 0.2s ease;}
.asset-card:hover .asset-footer {color: #FFD700;}

.modal-header {font-size: 20px; font-weight: 600; color: #1a1a1a; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 2px solid #FFD700;}
.modal-count {color: #999; font-weight: 400;}
</style>
""", unsafe_allow_html=True)

# ---------------- GOOGLE AUTH ----------------
@st.cache_resource
def load_credentials():
    try:
        credentials_dict = {
            key: (st.secrets["google_credentials"][key].replace('\\n', '\n') if key == "private_key" else st.secrets["google_credentials"][key])
            for key in st.secrets["google_credentials"]
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
            h1, h2 = row1_headers[i].strip(), row2_headers[i].strip()
            combined_headers.append(f"{h1} {h2}".strip() or "Unnamed")

        # ensure unique headers
        unique_headers, seen = [], {}
        for h in combined_headers:
            if h in seen:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                unique_headers.append(h)

        return pd.DataFrame(data[3:], columns=unique_headers)
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        return pd.DataFrame()

# ---------------- MAIN APP ----------------
st.markdown('<div class="header-title">Assets</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">List of assets in the commissary</div>', unsafe_allow_html=True)

credentials = load_credentials()
if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)

    if not df.empty:
        df = df.drop(df.columns[0], axis=1)
        station_col, asset_name_col, type_col = df.columns[1], df.columns[3], df.columns[2]
        stations = ['Hot Station', 'Fabrication Station', 'Pastry Station', 'Packing Station']

        # --- Restore modal state from query params ---
        query_params = st.experimental_get_query_params()
        if "station" in query_params and "asset" in query_params:
            modal_station = query_params["station"][0]
            modal_asset = query_params["asset"][0]
            modal_df = df[(df[station_col] == modal_station) & (df[asset_name_col] == modal_asset)]
            if not modal_df.empty:
                st.session_state[f"modal_{modal_station.replace(' ', '_')}"] = modal_asset
                st.session_state[f"modal_data_{modal_station.replace(' ', '_')}"] = modal_df

        tabs = st.tabs(stations)
        for tab, station_value in zip(tabs, stations):
            with tab:
                station_df = df[df[station_col] == station_value]
                station_key = station_value.replace(' ', '_')

                if f'modal_{station_key}' in st.session_state:
                    # Modal view
                    st.markdown(f'<div class="modal-header">← Back | {st.session_state[f"modal_{station_key}"]} <span class="modal-count">({len(st.session_state[f"modal_data_{station_key}"])} items)</span></div>', unsafe_allow_html=True)
                    if st.button("← Back", key=f"close_{station_key}"):
                        del st.session_state[f'modal_{station_key}']
                        del st.session_state[f'modal_data_{station_key}']
                        st.experimental_set_query_params()
                        st.rerun()

                    for _, row in st.session_state[f'modal_data_{station_key}'].iterrows():
                        with st.expander(row.get(df.columns[0], 'N/A')):
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
                    type_tabs = st.tabs(['Tools', 'Equipment'])
                    for type_tab, type_option in zip(type_tabs, ['Tools', 'Equipment']):
                        with type_tab:
                            filtered = station_df[station_df[type_col].str.contains(type_option, case=False, na=False)]
                            asset_names = ['All'] + sorted(filtered[asset_name_col].unique().tolist())
                            selected_asset = st.selectbox("Filter by Asset Name", options=asset_names, key=f"filter_{station_value}_{type_option}")
                            if selected_asset != 'All':
                                filtered = filtered[filtered[asset_name_col] == selected_asset]

                            grouped = filtered.groupby(asset_name_col)
                            num_cols = 4
                            for i, (asset_name, group_df) in enumerate(grouped):
                                cols = st.columns(num_cols)
                                for col_idx, col in enumerate(cols):
                                    if i + col_idx >= len(grouped): break
                                    count = len(group_df)
                                    safe_name = f"{station_key}_{type_option}_{i}_{col_idx}"
                                    card_color = 'card-dark'

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

                                    st.markdown("""
                                    <style>
                                    .element-container:has(> .stButton) { position: relative; margin-top: -200px; margin-bottom: 110px; z-index: 10; }
                                    .element-container:has(> .stButton) button { width: 100%; height: 200px; opacity: 0; cursor: pointer; background: transparent !important; border: none !important; }
                                    </style>
                                    """, unsafe_allow_html=True)

                                    if st.button(" ", key=f"{safe_name}_{asset_name}", use_container_width=True):
                                        st.session_state[f'modal_{station_key}'] = asset_name
                                        st.session_state[f'modal_data_{station_key}'] = group_df
                                        st.experimental_set_query_params(station=station_value, asset=asset_name)
                                        st.rerun()
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
