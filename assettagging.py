import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')
st.set_page_config(page_title="BOM Explosion", layout="wide")

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
st.title("Asset Tagging")

# Load credentials
credentials = load_credentials()

if credentials:
    # Input for Google Sheet URL
    sheet_url = "https://docs.google.com/spreadsheets/d/10GM76b6Y91ZfNelelaOvgXSLbqaPKHwfgMWN0x9Y42c"

    
    if sheet_url:
        # Load data from sheet index 0
        with st.spinner("Loading data from Google Sheets..."):
            df = load_sheet_data(credentials, sheet_url, sheet_index=0)
        
        if not df.empty:
            # Display dataframe info
            st.success(f"✅ Successfully loaded data from Sheet Index 0")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Sheet Index", 0)
            
            # Display the dataframe
            st.subheader("📋 Dataframe")
            st.dataframe(df, use_container_width=True)
            
            # Additional options
            with st.expander("🔍 View Data Info"):
                st.write("**Column Names:**")
                st.write(list(df.columns))
                st.write("**Data Types:**")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="spreadsheet_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data found in the sheet or an error occurred.")
else:
    st.error("Failed to load credentials. Please check your secrets configuration.")
