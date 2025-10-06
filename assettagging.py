import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Asset Tagging", layout="wide")

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
        
        # Combine rows 2 and 3 (index 1 and 2) to create headers
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
        
        # Make headers unique
        unique_headers = []
        header_counts = {}
        
        for header in combined_headers:
            if header in header_counts:
                header_counts[header] += 1
                unique_headers.append(f"{header}_{header_counts[header]}")
            else:
                header_counts[header] = 0
                unique_headers.append(header)
        
        # Create dataframe with data starting from row 4 (index 3)
        df = pd.DataFrame(data[3:], columns=unique_headers)
        
        return df
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        return pd.DataFrame()

# Main App
st.title("🏷️ Asset Tagging")

credentials = load_credentials()

if credentials:
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    
    with st.spinner("Loading data..."):
        df = load_sheet_data(credentials, sheet_url, sheet_index=0)
    
    if not df.empty:
        st.success(f"✅ Loaded {len(df)} rows")
        
        # Remove Column A (index 0)
        df = df.drop(df.columns[0], axis=1)
        
        # Column C is now index 1 after removing column A, Column E is now index 3
        station_col = df.columns[1]
        asset_name_col = df.columns[3]
        
        # Define stations - MUST MATCH EXACTLY with capital letters
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
                # Filter where column C equals the station value
                station_df = df[df[station_col] == station_value]
                
                if not station_df.empty:
                    # Get unique asset names for this station
                    asset_names = ['All'] + sorted(station_df[asset_name_col].unique().tolist())
                    
                    # Asset name filter
                    selected_asset = st.selectbox(
                        "Filter by Asset Name:",
                        options=asset_names,
                        key=f"filter_{station_value}"
                    )
                    
                    # Apply asset name filter
                    if selected_asset == 'All':
                        filtered = station_df
                    else:
                        filtered = station_df[station_df[asset_name_col] == selected_asset]
                    
                    st.metric("Rows", len(filtered))
                    st.dataframe(filtered, use_container_width=True)
                    
                    csv = filtered.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{station_value.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"btn_{station_value}"
                    )
                else:
                    st.warning(f"No rows found for {station_value}")
    else:
        st.error("No data loaded")
else:
    st.error("Failed to load credentials")
