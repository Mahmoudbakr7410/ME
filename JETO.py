import streamlit as st
import pandas as pd
import numpy as np
import logging
import math
from io import StringIO
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime

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
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'auth_threshold' not in st.session_state:
    st.session_state.auth_threshold = 10000
if 'suspicious_keywords' not in st.session_state:  # New session state variable for keywords
    st.session_state.suspicious_keywords = []

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

# Function to check for 99999 pattern
def is_99999(value):
    try:
        value = float(value)
        # Check if the value ends with 99999 (e.g., 999.99, 9999.99, 99999.99)
        return abs(value - round(value, 0)) >= 0.999 and abs(value - round(value, 0)) < 1.0
    except (ValueError, TypeError):
        return False

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

        # Check for entries just below authorization threshold
        if st.session_state.auth_threshold_var:
            threshold = st.session_state.auth_threshold
            below_threshold_entries = st.session_state.processed_df[
                (st.session_state.processed_df["Debit Amount (Dr)"] >= threshold * 0.9) & 
                (st.session_state.processed_df["Debit Amount (Dr)"] < threshold) |
                (st.session_state.processed_df["Credit Amount (Cr)"] >= threshold * 0.9) & 
                (st.session_state.processed_df["Credit Amount (Cr)"] < threshold)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, below_threshold_entries])

        # Check for 99999 pattern
        if st.session_state.nine_pattern_var:
            nine_pattern_entries = st.session_state.processed_df[
                st.session_state.processed_df["Debit Amount (Dr)"].apply(is_99999) |
                st.session_state.processed_df["Credit Amount (Cr)"].apply(is_99999)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, nine_pattern_entries])

        # Check for suspicious keywords
        if st.session_state.keywords_var:
            if "Entry Description" in st.session_state.processed_df.columns:
                if not st.session_state.suspicious_keywords:
                    st.warning("No suspicious keywords provided. Skipping keyword check.")
                else:
                    keyword_entries = st.session_state.processed_df[
                        st.session_state.processed_df["Entry Description"].str.contains(
                            "|".join(st.session_state.suspicious_keywords), case=False, na=False
                        )
                    ]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, keyword_entries])
            else:
                st.error("Column 'Entry Description' not found in the data.")
                return

        if not st.session_state.high_risk_entries.empty:
            st.success(f"Found {len(st.session_state.high_risk_entries)} high-risk entries.")
        else:
            st.success("No high-risk entries found.")
    except Exception as e:
        st.error(f"Error during testing: {e}")
        logging.error(f"Error during high-risk testing: {e}")

# Authentication
def login():
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        .login-box {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            max-width: 400px;
            margin: auto;
        }
        .login-box h2 {
            text-align: center;
            color: #2c3e50;
        }
        .login-box input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .login-box button {
            width: 100%;
            padding: 10px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .login-box button:hover {
            background-color: #2980b9;
        }
        .footer {
            position: fixed;
            left: 10px;
            bottom: 10px;
            font-size: 12px;
            color: #666;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Login box
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.image("https://res.cloudinary.com/dwtw5d4kq/image/upload/v1740139683/cropped-oie_NfAWRTRKjjnC-1_c8my9c.png", use_container_width=True)  # Your logo
    st.markdown("<h2>Login</h2>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "m.elansary@maham.com" and password == "123456789":
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer with developer credits
    st.markdown("<div class='footer'>Developed by Innovation and Transformation Team: Mahmoud Elansary and Sabeeh Uddin</div>", unsafe_allow_html=True)

# Streamlit UI
def main_app():
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
    st.session_state.auth_threshold_var = st.checkbox("Entries Just Below Authorization Threshold")
    st.session_state.nine_pattern_var = st.checkbox("99999 Pattern")
    st.session_state.keywords_var = st.checkbox("Suspicious Keywords")  # New checkbox for keywords

    if st.session_state.public_holidays_var:
        public_holidays_input = st.text_area("Enter Public Holidays (YYYY-MM-DD):", "Enter one date per line, e.g.:\n2023-01-01\n2023-12-25").strip().split("\n")
        st.session_state.public_holidays = []
        for date in public_holidays_input:
            if date.strip():  # Skip empty lines
                try:
                    parsed_date = pd.to_datetime(date.strip(), format="%Y-%m-%d")
                    st.session_state.public_holidays.append(parsed_date)
                except ValueError:
                    st.error(f"Invalid date format: {date.strip()}. Please use the format YYYY-MM-DD.")

    if st.session_state.rounded_var:
        st.session_state.rounded_threshold = st.number_input("Enter Threshold for Rounded Numbers:", value=100.0)

    if st.session_state.unusual_users_var:
        st.session_state.authorized_users = st.text_input("Enter Authorized Users (comma-separated):", "").strip().split(",")
        st.session_state.authorized_users = [user.strip() for user in st.session_state.authorized_users if user.strip()]

    if st.session_state.post_closing_var:
        st.session_state.closing_date = st.date_input("Enter Closing Date of the Books (YYYY-MM-DD):")

    if st.session_state.auth_threshold_var:
        st.session_state.auth_threshold = st.number_input("Enter Authorization Threshold Amount:", value=10000.0)

    if st.session_state.keywords_var:  # New input for suspicious keywords
        st.session_state.suspicious_keywords = st.text_area(
            "Enter Suspicious Keywords (comma-separated):",
            "miscellaneous, adjustment, correction, other, rounding"
        ).strip().split(",")
        st.session_state.suspicious_keywords = [keyword.strip().lower() for keyword in st.session_state.suspicious_keywords if keyword.strip()]

    if st.button("Run Test"):
        perform_high_risk_test()

    # Data Visualization
    if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
        st.header("Data Visualization")
        
        # Plotting the high-risk entries using Plotly
        st.subheader("Interactive Bar Chart: Debit vs Credit Amounts")
        fig = px.bar(st.session_state.high_risk_entries, x="Transaction ID", y=["Debit Amount (Dr)", "Credit Amount (Cr)"],
                     barmode='group', title="High-Risk Entries: Debit vs Credit Amounts")
        st.plotly_chart(fig)

        # Plotting a scatter plot for Debit vs Credit Amounts
        st.subheader("Scatter Plot: Debit vs Credit Amounts")
        fig2 = px.scatter(st.session_state.high_risk_entries, x="Debit Amount (Dr)", y="Credit Amount (Cr)",
                          color="Transaction ID", title="Scatter Plot of Debit vs Credit Amounts")
        st.plotly_chart(fig2)

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

# Check if user is logged in
if not st.session_state.logged_in:
    login()
else:
    main_app()
