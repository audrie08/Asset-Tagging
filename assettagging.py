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
    .header-title {font-size: 28px;font-weight: 600;color: #1a1a1a;margin-bottom: 0.25rem;}
    .header-subtitle {font-size: 14px;color: #666;margin-bottom: 2rem;}
    .modal-header {font-size: 20px;font-weight: 600;color: #1a1a1a;margin-bottom: 1rem;padding-bottom: 0.75rem;border-bottom: 2px solid #FFD700;}
    .modal-count {color: #999;font-weight: 400;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# FUNCTIONS
# -----------------------------
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
            h1 = row1_headers[i].strip() if i < len(row1_headers) else ''
            h2 = row2_headers[i].strip() if i < len(row2_headers) else ''
            combined = f"{h1} {h2}".strip() if h1 or h2 else "Unnamed"
            combined_headers.append(combined)

        unique_headers, counts = [], {}
        for h in combined_headers:
            if h in counts:
                counts[h] += 1
                unique_headers.append(f"{h}_{counts[h]}")
            else:
                counts[h] = 0
                unique_headers.append(h)

        df = pd.DataFrame(data[3:], columns=unique_headers)
        return df
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        return pd.DataFrame()

# -----------------------------
# MAIN UI
# -----------------------------
st.markdown('<div class="header-title">Assets</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">List of assets in the commissary</div>', unsafe_allow_html=True)

credentials = load_credentials()
if not credentials:
    st.error("Failed to load credentials")
    st.stop()

sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
with st.spinner("Loading data..."):
    df = load_sheet_data(credentials, sheet_url)

if df.empty:
    st.error("No data loaded")
    st.stop()

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

# Track last selected tab to clear modal when switching
if "last_tab" not in st.session_state:
    st.session_state["last_tab"] = None

tabs = st.tabs(list(stations.keys()))

for tab, (tab_name, station_value) in zip(tabs, stations.items()):
    with tab:
        # Detect tab switch and clear modal state if needed
        if st.session_state["last_tab"] != tab_name:
            # Clear all modal keys
            for key in list(st.session_state.keys()):
                if key.startswith("modal_"):
                    st.session_state.pop(key, None)
            st.session_state["last_tab"] = tab_name

        station_df = df[df[station_col] == station_value]
        if station_df.empty:
            st.info("No assets found.")
            continue

        station_key = station_value.replace(' ', '_')

        # -------------------
        # MODAL VIEW
        # -------------------
        if f'modal_{station_key}' in st.session_state:
            asset_name = st.session_state[f"modal_{station_key}"]
            asset_data = st.session_state[f"modal_data_{station_key}"]

            st.markdown(
                f'<div class="modal-header">{asset_name} <span class="modal-count">({len(asset_data)} items)</span></div>',
                unsafe_allow_html=True
            )

            if st.button("← Back to Asset List", key=f"back_{station_key}"):
                st.session_state.pop(f"modal_{station_key}", None)
                st.session_state.pop(f"modal_data_{station_key}", None)
                st.rerun()

            st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

            for idx, row in asset_data.iterrows():
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

        # -------------------
        # LIST VIEW
        # -------------------
        else:
            type_options = ['All', 'Tools', 'Equipment']
            type_tabs = st.tabs(type_options)

            for type_tab, type_option in zip(type_tabs, type_options):
                with type_tab:
                    filtered = station_df.copy()
                    if type_option != 'All':
                        filtered = filtered[filtered[type_col].str.contains(type_option, case=False, na=False)]

                    asset_names = ['All'] + sorted(filtered[asset_name_col].unique().tolist())
                    selected_asset = st.selectbox(
                        "Filter by Asset Name", 
                        options=asset_names, 
                        key=f"filter_{station_value}_{type_option}"
                    )

                    if selected_asset != 'All':
                        filtered = filtered[filtered[asset_name_col] == selected_asset]

                    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

                    if filtered.empty:
                        st.info("No assets found.")
                        continue

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
                                    background: transparent !important;
                                    border: none !important;
                                }
                                </style>
                                """, unsafe_allow_html=True)

                                if st.button(" ", key=f"{safe_name}_{asset_name}", use_container_width=True):
                                    st.session_state[f'modal_{station_key}'] = asset_name
                                    st.session_state[f'modal_data_{station_key}'] = group_df
                                    st.rerun()
