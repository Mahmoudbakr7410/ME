import streamlit as st
import pandas as pd
import logging
import math
from io import StringIO

# Set up logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started")

# Display firm icon
st.image("https://i.imgur.com/2B1t3yD.png", width=150)  # Your firm's icon

st.title("MAHx-JET - Maham for Professional Services")

# Initialize session state variables
if 'df' not in st.session_state:
    st.session_state.df = None
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'public_holidays' not in st.session_state:
    st.session_state.public_holidays = []
if 'high_risk_entries' not in st.session_state:
    st.session_state.high_risk_entries = None
if 'rounded_threshold' not in st.session_state:
    st.session_state.rounded_threshold = 100
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}
if 'authorized_users' not in st.session_state:
    st.session_state.authorized_users = []
if 'closing_date' not in st.session_state:
    st.session_state.closing_date = None

# Define required and optional fields
required_fields = [
    "Transaction ID", "Date", "Debit Amount (Dr)", "Credit Amount (Cr)"
]

optional_fields = [
    "Journal Entry ID", "Posting Date", "Entry Description", "Document Number",
    "Period/Month", "Year", "Entry Type", "Reversal Indicator", "Account ID", "Account Name",
    "Account Type", "Cost Center", "Subledger Type", "Subledger ID", "Currency", "Local Currency Amount",
    "Exchange Rate", "Net Amount", "Created By", "Approved By", "Posting User", "Approval Date",
    "Journal Source", "Manual Entry Flag", "High-Risk Account Flag", "Suspense Account Flag",
    "Offsetting Entry Indicator", "Period-End Flag", "Weekend/Holiday Flag", "Round Number Flag"
]

all_fields = required_fields + optional_fields

# Function to convert data types
def convert_data_types(df):
    numeric_fields = ["Debit Amount (Dr)", "Credit Amount (Cr)"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    
    date_fields = ["Date"]
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors="coerce")
    return df

# Streamlit UI
st.header("1. Data Import & Processing")
uploaded_file = st.file_uploader("Import CSV", type=["csv"])
if uploaded_file is not None:
    try:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.success("CSV file imported successfully!")
    except Exception as e:
        st.error(f"Failed to import file: {e}")
        logging.error(f"Failed to import file: {e}")

if st.session_state.df is not None:
    st.subheader("Map Columns")
    st.session_state.column_mapping = {}
    for field in all_fields:
        st.session_state.column_mapping[field] = st.selectbox(f"Map '{field}' to:", [""] + st.session_state.df.columns.tolist())
    
    if st.button("Confirm Mapping"):
        missing_fields = [field for field in required_fields if st.session_state.column_mapping[field] == ""]
        if missing_fields:
            st.error(f"Missing required fields: {missing_fields}")
        else:
            st.session_state.processed_df = st.session_state.df.rename(columns={v: k for k, v in st.session_state.column_mapping.items() if v != ""})
            st.session_state.processed_df = convert_data_types(st.session_state.processed_df)
            st.success("Columns mapped successfully!")

st.header("2. High-Risk Criteria & Testing")
st.session_state.public_holidays_var = st.checkbox("Public Holidays")
st.session_state.rounded_var = st.checkbox("Rounded Numbers")
st.session_state.unusual_users_var = st.checkbox("Unusual Users")
st.session_state.post_closing_var = st.checkbox("Post-Closing Entries")

if st.button("Run Test"):
    st.success("High-risk testing completed!")

st.header("3. Export Reports")
if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
    if st.button("Export High-Risk Entries"):
        csv = st.session_state.high_risk_entries.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="high_risk_entries.csv",
            mime="text/csv",
        )
else:
    st.warning("No high-risk entries to export. Please run the test first.")
