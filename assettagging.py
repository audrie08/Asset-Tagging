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
            
            # Combine the two rows
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
        
        # Remove completely empty columns
        df = df.loc[:, (df != '').any(axis=0)]
        
        return df
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        return pd.DataFrame()

# Main App
st.title("🏷️ Asset Tagging - Station Filter")

# Load credentials
credentials = load_credentials()

if credentials:
    # Input for Google Sheet URL
    sheet_url = st.text_input(
        "Enter Google Sheet URL:",
        value="https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"
    )
    
    if sheet_url:
        # Load data from sheet index 0
        with st.spinner("Loading data from Google Sheets..."):
            df = load_sheet_data(credentials, sheet_url, sheet_index=0)
        
        if not df.empty:
            st.success(f"✅ Successfully loaded data from Sheet Index 0")
            
            # Let user select which column contains station info
            st.subheader("🔧 Filter Configuration")
            station_column = st.selectbox(
                "Select the column that contains station information:",
                options=df.columns.tolist(),
                index=0
            )
            
            # Define stations
            stations = ['hot', 'fabrication', 'pastry', 'packing']
            
            # Create tabs for each station
            st.subheader("🏭 Station Data")
            tabs = st.tabs(['All Data'] + [s.title() for s in stations])
            
            # All Data tab
            with tabs[0]:
                st.metric("Total Rows", len(df))
                st.dataframe(df, use_container_width=True)
                
                csv_all = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Data",
                    data=csv_all,
                    file_name="all_stations_data.csv",
                    mime="text/csv"
                )
            
            # Individual station tabs
            for idx, station in enumerate(stations, 1):
                with tabs[idx]:
                    # Filter dataframe for this station (case-insensitive)
                    filtered_df = df[df[station_column].str.lower().str.contains(station, na=False)]
                    
                    if not filtered_df.empty:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(f"{station.title()} Rows", len(filtered_df))
                        with col2:
                            st.metric("Columns", len(filtered_df.columns))
                        
                        st.dataframe(filtered_df, use_container_width=True)
                        
                        # Download button for filtered data
                        csv_filtered = filtered_df.to_csv(index=False)
                        st.download_button(
                            label=f"📥 Download {station.title()} Data",
                            data=csv_filtered,
                            file_name=f"{station.replace(' ', '_')}_data.csv",
                            mime="text/csv",
                            key=f"download_{station}"
                        )
                    else:
                        st.warning(f"No data found for {station.title()}")
            
            # Additional options
            with st.expander("🔍 View Data Info"):
                st.write("**Column Names:**")
                st.write(list(df.columns))
                st.write("**Data Types:**")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
                
                st.write("**Station Distribution:**")
                if station_column in df.columns:
                    station_counts = df[station_column].value_counts()
                    st.dataframe(station_counts)
        else:
            st.warning("No data found in the sheet or an error occurred.")
else:
    st.error("Failed to load credentials. Please check your secrets configuration.")
