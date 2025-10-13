import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

# --- Page headers ---
st.markdown('<div class="header-title">Assets</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">List of assets in the commissary</div>', unsafe_allow_html=True)


# --- Credential + Sheet loader functions ---
def load_credentials():
    try:
        with open("service_account.json") as f:
            creds = Credentials.from_service_account_info(
                eval(f.read()),
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        return creds
    except Exception as e:
        st.error(f"Credential load error: {e}")
        return None


def load_sheet_data(credentials, sheet_url, sheet_index=0):
    try:
        client = gspread.authorize(credentials)
        sheet = client.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(sheet_index)
        data = worksheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Failed to load sheet: {e}")
        return pd.DataFrame()


# --- Main Logic ---
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

        # --- Restore modal state from query params (cross-version safe) ---
        query_params = st.experimental_get_query_params()
        if "station" in query_params and "asset" in query_params:
            modal_station = query_params["station"][0]
            modal_asset = query_params["asset"][0]
            modal_df = df[(df[station_col] == modal_station) & (df[asset_name_col] == modal_asset)]
            if not modal_df.empty:
                st.session_state[f"modal_{modal_station.replace(' ', '_')}"] = modal_asset
                st.session_state[f"modal_data_{modal_station.replace(' ', '_')}"] = modal_df

        tabs = st.tabs(list(stations.keys()))

        for tab, (tab_name, station_value) in zip(tabs, stations.items()):
            with tab:
                station_df = df[df[station_col] == station_value]

                if not station_df.empty:
                    station_key = station_value.replace(' ', '_')

                    # --- MODAL VIEW ---
                    if f'modal_{station_key}' in st.session_state:
                        st.markdown(
                            f'<div class="modal-header">'
                            f'<b>{st.session_state[f"modal_{station_key}"]}</b> '
                            f'<span class="modal-count">({len(st.session_state[f"modal_data_{station_key}"])} items)</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                        if st.button("← Back", key=f"close_{station_key}"):
                            del st.session_state[f'modal_{station_key}']
                            del st.session_state[f'modal_data_{station_key}']
                            st.experimental_set_query_params()  # clear params
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

                    # --- GRID VIEW ---
                    else:
                        type_col = df.columns[2]
                        type_options = ['Tools', 'Equipment']
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
                                                    st.experimental_set_query_params(
                                                        station=station_value,
                                                        asset=asset_name
                                                    )
                                                    st.rerun()
                                else:
                                    st.info("No assets found")

    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
