import streamlit as st
import pandas as pd
import logging
import math
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns

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
    "Period/Month", "Year", "Entry Type", "Reversal Indicator", "Account ID", "Account Name",
    "Account Type", "Cost Center", "Subledger Type", "Subledger ID", "Currency", "Local Currency Amount",
    "Exchange Rate", "Net Amount", "Created By", "Approved By", "Posting User", "Approval Date",
    "Journal Source", "Manual Entry Flag", "High-Risk Account Flag", "Suspense Account Flag",
    "Offsetting Entry Indicator", "Period-End Flag", "Weekend/Holiday Flag", "Round Number Flag"
]

all_fields = required_fields + optional_fields

# Function to convert data types
def convert_data_types(df):
    # Convert numeric fields
    numeric_fields = ["Debit Amount (Dr)", "Credit Amount (Cr)"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")

    # Convert date fields
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
        # Initialize high-risk entries
        st.session_state.high_risk_entries = pd.DataFrame()

        # Check for public holiday entries
        if st.session_state.public_holidays_var:
            if "Date" in st.session_state.processed_df.columns:
                holiday_entries = st.session_state.processed_df[st.session_state.processed_df["Date"].isin(st.session_state.public_holidays)]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, holiday_entries])
            else:
                st.error("Column 'Date' not found in the data.")
                return

        # Check for rounded numbers
        if st.session_state.rounded_var:
            def is_rounded(value, threshold):
                try:
                    value = float(value)  # Ensure value is numeric
                    if value == 0:
                        return False  # Ignore zero values
                    return (value % threshold == 0) or (math.isclose(value % threshold, threshold, rel_tol=1e-6))
                except (ValueError, TypeError):
                    return False  # Ignore non-numeric values

            rounded_entries = st.session_state.processed_df[
                st.session_state.processed_df["Debit Amount (Dr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold)) |
                st.session_state.processed_df["Credit Amount (Cr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold))
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, rounded_entries])

        # Check for unusual users
        if st.session_state.unusual_users_var:
            if "Created By" in st.session_state.processed_df.columns:
                # Ensure authorized_users is not empty
                if not st.session_state.authorized_users:
                    st.warning("No authorized users provided. Skipping unusual users check.")
                else:
                    unusual_user_entries = st.session_state.processed_df[~st.session_state.processed_df["Created By"].isin(st.session_state.authorized_users)]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, unusual_user_entries])
            else:
                st.error("Column 'Created By' not found in the data.")
                return

        # Check for post-closing entries
        if st.session_state.post_closing_var:
            if "Date" in st.session_state.processed_df.columns:
                if st.session_state.closing_date is None:
                    st.warning("No closing date provided. Skipping post-closing entries check.")
                else:
                    post_closing_entries = st.session_state.processed_df[st.session_state.processed_df["Date"] > st.session_state.closing_date]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, post_closing_entries])
            else:
                st.error("Column 'Date' not found in the data.")
                return

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

# High-Risk Criteria & Testing
st.header("2. High-Risk Criteria & Testing")
st.session_state.public_holidays_var = st.checkbox("Public Holidays")
st.session_state.rounded_var = st.checkbox("Rounded Numbers")
st.session_state.unusual_users_var = st.checkbox("Unusual Users")
st.session_state.post_closing_var = st.checkbox("Post-Closing Entries")

if st.session_state.public_holidays_var:
    st.session_state.public_holidays = st.text_area("Enter Public Holidays (YYYY-MM-DD):", "Enter one date per line, e.g.:\n2023-01-01\n2023-12-25").strip().split("\n")
    st.session_state.public_holidays = [pd.to_datetime(date.strip()) for date in st.session_state.public_holidays if date.strip()]

if st.session_state.rounded_var:
    st.session_state.rounded_threshold = st.number_input("Enter Threshold for Rounded Numbers:", value=100.0)

if st.session_state.unusual_users_var:
    st.session_state.authorized_users = st.text_input("Enter Authorized Users (comma-separated):", "").strip().split(",")
    st.session_state.authorized_users = [user.strip() for user in st.session_state.authorized_users if user.strip()]

if st.session_state.post_closing_var:
    st.session_state.closing_date = st.date_input("Enter Closing Date of the Books (YYYY-MM-DD):")

if st.button("Run Test"):
    perform_high_risk_test()

# Data Visualization
st.header("Data Visualization")

if st.session_state.processed_df is not None and not st.session_state.processed_df.empty:
    st.subheader("Debit vs Credit Amounts")
    fig, ax = plt.subplots()
    sns.scatterplot(data=st.session_state.processed_df, x="Debit Amount (Dr)", y="Credit Amount (Cr)", ax=ax)
    st.pyplot(fig)

    st.subheader("Distribution of Debit Amounts")
    fig, ax = plt.subplots()
    sns.histplot(st.session_state.processed_df["Debit Amount (Dr)"].dropna(), kde=True, ax=ax)
    st.pyplot(fig)

    st.subheader("Distribution of Credit Amounts")
    fig, ax = plt.subplots()
    sns.histplot(st.session_state.processed_df["Credit Amount (Cr)"].dropna(), kde=True, ax=ax)
    st.pyplot(fig)

if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
    st.subheader("High-Risk Entries by Date")
    fig, ax = plt.subplots()
    sns.countplot(data=st.session_state.high_risk_entries, x="Date", ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Export Reports
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

# Guide
st.sidebar.header("Guide")
st.sidebar.markdown("""
**Journal Entry Testing Guide**

The following fields are required for testing:
- Transaction ID
- Date
- Debit Amount (Dr)
- Credit Amount (Cr)

**Steps:**
1. Import a CSV file containing the required fields.
2. Map the CSV columns to the required fields.
3. Set high-risk criteria (e.g., public holidays, rounded numbers, unusual users, post-closing entries).
4. Run the test to identify high-risk entries.
5. Export the results to a CSV file.
""")

# Preview Data
if st.session_state.processed_df is not None and not st.session_state.processed_df.empty:
    st.header("Preview Data")
    st.dataframe(st.session_state.processed_df.head(10))
