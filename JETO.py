import streamlit as st
import pandas as pd
import logging
import math
from io import StringIO

# Set up logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started")

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
    "Created By", "Approved By", "Weekend/Holiday Flag", "Suspense Account Flag"
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

# Function to perform high-risk testing
def perform_high_risk_test():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to test. Please import a CSV file first.")
        return

    try:
        st.session_state.high_risk_entries = pd.DataFrame()

        # Public holiday entries
        if st.session_state.public_holidays_var and "Date" in st.session_state.processed_df.columns:
            holiday_entries = st.session_state.processed_df[st.session_state.processed_df["Date"].isin(st.session_state.public_holidays)]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, holiday_entries])

        # Rounded numbers
        if st.session_state.rounded_var:
            def is_rounded(value, threshold):
                try:
                    value = float(value)
                    return (value % threshold == 0) or (math.isclose(value % threshold, threshold, rel_tol=1e-6))
                except (ValueError, TypeError):
                    return False

            rounded_entries = st.session_state.processed_df[
                st.session_state.processed_df["Debit Amount (Dr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold)) |
                st.session_state.processed_df["Credit Amount (Cr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold))
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, rounded_entries])

        # Large Transactions
        if st.session_state.large_transactions_var:
            large_entries = st.session_state.processed_df[
                (st.session_state.processed_df["Debit Amount (Dr)"] >= st.session_state.large_threshold) |
                (st.session_state.processed_df["Credit Amount (Cr)"] >= st.session_state.large_threshold)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, large_entries])

        # Unusual Users
        if st.session_state.unusual_users_var and "Created By" in st.session_state.processed_df.columns:
            unusual_user_entries = st.session_state.processed_df[
                ~st.session_state.processed_df["Created By"].isin(st.session_state.authorized_users)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, unusual_user_entries])

        # Post-Closing Entries
        if st.session_state.post_closing_var and "Date" in st.session_state.processed_df.columns and st.session_state.closing_date:
            post_closing_entries = st.session_state.processed_df[
                st.session_state.processed_df["Date"] > st.session_state.closing_date
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, post_closing_entries])

        if not st.session_state.high_risk_entries.empty:
            st.success(f"Found {len(st.session_state.high_risk_entries)} high-risk entries.")
        else:
            st.success("No high-risk entries found.")

    except Exception as e:
        st.error(f"Error during testing: {e}")
        logging.error(f"Error during high-risk testing: {e}")

# Streamlit UI
st.title("MAHx-JET - Maham for Professional Services")

# Data Import & Processing
st.header("1. Data Import & Processing")
uploaded_file = st.file_uploader("Import CSV", type=["csv"])
if uploaded_file is not None:
    try:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.success("CSV file imported successfully!")
    except Exception as e:
        st.error(f"Failed to import file: {e}")

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

# High-Risk Criteria & Testing
st.header("2. High-Risk Criteria & Testing")
st.session_state.public_holidays_var = st.checkbox("Public Holidays")
st.session_state.rounded_var = st.checkbox("Rounded Numbers")
st.session_state.large_transactions_var = st.checkbox("Large Transactions")
st.session_state.unusual_users_var = st.checkbox("Unusual Users")
st.session_state.post_closing_var = st.checkbox("Post-Closing Entries")

if st.session_state.large_transactions_var:
    st.session_state.large_threshold = st.number_input("Enter Large Transaction Threshold:", value=100000.0)

if st.button("Run Test"):
    perform_high_risk_test()

# Export Reports
st.header("3. Export Reports")
if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
    csv = st.session_state.high_risk_entries.to_csv(index=False)
    st.download_button(
        label="Download High-Risk Entries CSV",
        data=csv,
        file_name="high_risk_entries.csv",
        mime="text/csv",
    )
else:
    st.warning("No high-risk entries to export.")

# Guide
st.sidebar.header("Guide")
st.sidebar.markdown("### How to Use MAHx-JET\n1. Upload a CSV file.\n2. Map required columns.\n3. Select high-risk criteria.\n4. Run tests.\n5. Export results.")

# Preview Data
if st.session_state.processed_df is not None:
    st.header("Preview Data")
    st.dataframe(st.session_state.processed_df.head(10))
