import streamlit as st
import pandas as pd
import numpy as np
import logging
import math
from io import StringIO, BytesIO
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
from fpdf import FPDF  # For PDF export
from sklearn.cluster import KMeans  # For pattern recognition
from sklearn.preprocessing import StandardScaler  # For scaling data
import csv  # For delimiter detection
import dask.dataframe as dd  # For memory-efficient data processing
import psutil  # For memory profiling
import multiprocessing as mp  # For multiprocessing

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
if 'suspicious_keywords' not in st.session_state:
    st.session_state.suspicious_keywords = []
if 'trial_balance' not in st.session_state:
    st.session_state.trial_balance = None
if 'completeness_check_results' not in st.session_state:
    st.session_state.completeness_check_results = None
if 'completeness_check_passed' not in st.session_state:
    st.session_state.completeness_check_passed = False
if 'audited_client_name' not in st.session_state:
    st.session_state.audited_client_name = ""
if 'year_audited' not in st.session_state:
    st.session_state.year_audited = datetime.now().year
if 'flagged_entries_by_category' not in st.session_state:
    st.session_state.flagged_entries_by_category = {}
if 'pattern_recognition_results' not in st.session_state:
    st.session_state.pattern_recognition_results = None
if 'seldomly_used_accounts_threshold' not in st.session_state:
    st.session_state.seldomly_used_accounts_threshold = 5

# Define authorized users
authorized_users = {
    "a.habbul@maham.com": "password1",
    "a.elnahal@maham.com": "password2",
    "a.younes@maham.com": "password3",
    "a.alhazmi@maham.com": "password4",
    "a.almousa@maham.com": "password5",
    "a.alqadi@maham.com": "password6",
    "a.alqahtani@maham.com": "password7",
    "a.alrubayan@maham.com": "password8",
    "a.alamodi@maham.com": "password9",
    "a.alremawi@maham.com": "password10",
    "a.abdelgawad@maham.com": "password11",
    "a.alwhaibi@maham.com": "password12",
    "a.elnouby@maham.com": "password13",
    "a.goma@maham.com": "password14",
    "a.magdi@maham.com": "password15",
    "a.nagy@maham.com": "password16",
    "a.basith@maham.com": "password17",
    "a.alali@maham.com": "password18",
    "a.arafat@maham.com": "password19",
    "a.shedeed@maham.com": "password20",
    "a.salem@maham.com": "password21",
    "a.khan@maham.com": "password22",
    "E.Alshehri@maham.com": "password23",
    "f.alkaltham@maham.com": "password24",
    "f.alanazi@maham.com": "password25",
    "f.muhammad@maham.com": "password26",
    "I.abdulwahab@maham.com": "password27",
    "i.alabdullah@maham.com": "password28",
    "i.alotaibi@maham.com": "password29",
    "i.metwally@maham.com": "password30",
    "j.rizkallah@maham.com": "password31",
    "kh.almatroudi@maham.com": "password32",
    "l.Alrizqi@maham.com": "password33",
    "l.altuwaim@maham.com": "password34",
    "m.abead@maham.com": "password35",
    "m.abdelrahim@maham.com": "password36",
    "m.elansary@maham.com": "74107410",
    "m.hamouda@maham.com": "password37",
    "m.mostafa@maham.com": "password38",
    "m.noman@maham.com": "password39",
    "m.erman@maham.com": "password40",
    "m.alqattan@maham.com": "password41",
    "m.alrashidi@maham.com": "password42",
    "M.Alshammari@maham.com": "password43",
    "m.bilal@maham.com": "password44",
    "m.zain@maham.com": "password45",
    "m.alangari@maham.com": "password46",
    "m.attia@maham.com": "password47",
    "m.Thafseem@maham.com": "password48",
    "m.masood@maham.com": "password49",
    "m.Alshehri@maham.com": "password50",
    "n.adham@maham.com": "password51",
    "n.alsayeh@maham.com": "password52",
    "n.sabhah@maham.com": "password53",
    "o.almatrudi@maham.com": "password54",
    "r.alabdulhadi@maham.com": "password55",
    "r.alhamidi@maham.com": "password56",
    "r.aljebali@maham.com": "password57",
    "s.uddin@maham.com": "password58",
    "s.alharbi@maham.com": "password59",
    "s.salih@maham.com": "password60",
    "s.ahmed@maham.com": "password61",
    "s.alqadi@maham.com": "password62",
    "s.lashaera@maham.com": "password63",
    "sh.alanazi@maham.com": "password64",
    "s.alhalal@maham.com": "password65",
    "t.alhassan@maham.com": "password66",
    "u.riaz@maham.com": "password67",
    "w.alanazi@maham.com": "password68",
    "s.habib@maham.com": "internalaudit@2025",
    "y.alahmadi@maham.com": "password69"
}

# Define required and optional fields
required_fields = [
    "Transaction ID", "Date", "Debit Amount (Dr)", "Credit Amount (Cr)", "Account Number"
]

optional_fields = [
    "Journal Entry ID", "Posting Date", "Entry Description", "Document Number",
    "Period/Month", "Year", "Entry Type", "Reversal Indicator", "Account Name",
    "Account Type", "Cost Center", "Subledger Type", "Subledger ID", "Currency", "Local Currency Amount",
    "Exchange Rate", "Net Amount", "Created By", "Approved By", "Posting User", "Approval Date",
    "Journal Source", "Manual Entry Flag", "High-Risk Account Flag", "Suspense Account Flag",
    "Offsetting Entry Indicator", "Period-End Flag", "Weekend/Holiday Flag", "Round Number Flag"
]

all_fields = required_fields + optional_fields

# Function to detect delimiter for txt files
def detect_delimiter(file):
    sample = file.read(1024).decode('utf-8')
    file.seek(0)
    sniffer = csv.Sniffer()
    delimiter = sniffer.sniff(sample).delimiter
    return delimiter

# Function to convert data types
@st.cache_data
def convert_data_types(df):
    numeric_fields = ["Debit Amount (Dr)", "Credit Amount (Cr)"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce").astype('float32')
    date_fields = ["Date"]
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors="coerce")
    return df

# Function to process data in chunks
def process_data_in_chunks(file, chunk_size=100000):
    chunks = pd.read_csv(file, chunksize=chunk_size)
    processed_chunks = []
    progress_bar = st.progress(0)
    for i, chunk in enumerate(chunks):
        chunk = convert_data_types(chunk)
        processed_chunks.append(chunk)
        progress_bar.progress((i + 1) / len(chunks))
    return pd.concat(processed_chunks)

# Function to perform completeness check
@st.cache_data
def perform_completeness_check():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No GL data to test. Please import a file first.")
        return
    if st.session_state.trial_balance is None or st.session_state.trial_balance.empty:
        st.warning("No trial balance data to test. Please import a trial balance file first.")
        return

    try:
        gl_summary = st.session_state.processed_df.groupby("Account Number").agg(
            Total_Debits=("Debit Amount (Dr)", "sum"),
            Total_Credits=("Credit Amount (Cr)", "sum")
        ).reset_index()
        merged_df = pd.merge(
            st.session_state.trial_balance,
            gl_summary,
            on="Account Number",
            how="left"
        )
        merged_df["Total_Debits"] = merged_df["Total_Debits"].fillna(0)
        merged_df["Total_Credits"] = merged_df["Total_Credits"].fillna(0)
        merged_df["Expected_Ending_Balance"] = (
            merged_df["Opening Balance"] + merged_df["Total_Debits"] - merged_df["Total_Credits"]
        )
        merged_df["Discrepancy"] = (
            merged_df["Expected_Ending_Balance"] - merged_df["Ending Balance"]
        )
        st.session_state.completeness_check_results = merged_df
        max_discrepancy = merged_df["Discrepancy"].abs().max()
        if max_discrepancy <= 5:
            st.session_state.completeness_check_passed = True
            st.success("Completeness check passed! Maximum discrepancy is within the allowed tolerance of 5.")
        else:
            st.session_state.completeness_check_passed = False
            st.warning(f"Completeness check failed! Maximum discrepancy ({max_discrepancy}) exceeds the allowed tolerance of 5.")
        st.dataframe(merged_df)
        discrepancies = merged_df[abs(merged_df["Discrepancy"]) > 0.01]
        if not discrepancies.empty:
            st.warning(f"Found {len(discrepancies)} accounts with discrepancies.")
            st.dataframe(discrepancies)
        else:
            st.success("No discrepancies found. All accounts are complete.")
    except Exception as e:
        st.error(f"Error during completeness check: {e}")
        logging.error(f"Error during completeness check: {e}")

# Streamlit UI
def main_app():
    st.title("MAHAM DATA DEEP ANALYZER DEMO")

    # Data Import & Processing
    st.header("1. Data Import & Processing")
    uploaded_file = st.file_uploader("Import GL Dump File", type=["csv", "parquet", "txt"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state.df = process_data_in_chunks(uploaded_file)
            elif uploaded_file.name.endswith('.parquet'):
                st.session_state.df = pd.read_parquet(uploaded_file)
            elif uploaded_file.name.endswith('.txt'):
                delimiter = detect_delimiter(uploaded_file)
                st.session_state.df = pd.read_csv(uploaded_file, delimiter=delimiter)
            st.success("GL Dump file imported successfully!")
        except Exception as e:
            st.error(f"Failed to import file: {e}")
            logging.error(f"Failed to import file: {e}")

    # Import Trial Balance
    st.subheader("Import Trial Balance")
    tb_uploaded_file = st.file_uploader("Import Trial Balance File", type=["csv", "parquet", "txt"])
    if tb_uploaded_file is not None:
        try:
            if tb_uploaded_file.name.endswith('.csv'):
                st.session_state.trial_balance = pd.read_csv(tb_uploaded_file)
            elif tb_uploaded_file.name.endswith('.parquet'):
                st.session_state.trial_balance = pd.read_parquet(tb_uploaded_file)
            elif tb_uploaded_file.name.endswith('.txt'):
                delimiter = detect_delimiter(tb_uploaded_file)
                st.session_state.trial_balance = pd.read_csv(tb_uploaded_file, delimiter=delimiter)
            st.success("Trial Balance file imported successfully!")
        except Exception as e:
            st.error(f"Failed to import trial balance file: {e}")
            logging.error(f"Failed to import trial balance file: {e}")

    # Input audited client name and year
    st.session_state.audited_client_name = st.text_input("Enter Audited Client Name:", value=st.session_state.audited_client_name)
    st.session_state.year_audited = st.number_input("Enter Year Audited:", value=st.session_state.year_audited)

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

    # Completeness Check
    st.header("2. Completeness Check")
    if st.button("Run Completeness Check"):
        perform_completeness_check()

    # Data Mining and Pattern Recognition
    st.header("3. Data Mining and Pattern Recognition")
    if st.button("Run Pattern Recognition"):
        perform_pattern_recognition()

    # High-Risk Criteria & Testing
    st.header("4. High-Risk Criteria & Testing")
    if not st.session_state.completeness_check_passed:
        st.warning("High-risk tests are disabled until the completeness check passes with a maximum discrepancy of 5.")
    else:
        st.session_state.public_holidays_var = st.checkbox("Public Holidays")
        st.session_state.rounded_var = st.checkbox("Rounded Numbers")
        st.session_state.unusual_users_var = st.checkbox("Unusual Users")
        st.session_state.post_closing_var = st.checkbox("Post-Closing Entries")
        st.session_state.auth_threshold_var = st.checkbox("Entries Just Below Authorization Threshold")
        st.session_state.nine_pattern_var = st.checkbox("99999 Pattern")
        st.session_state.keywords_var = st.checkbox("Suspicious Keywords")
        st.session_state.seldomly_used_accounts_var = st.checkbox("Seldomly Used Accounts")

        if st.session_state.public_holidays_var:
            public_holidays_input = st.text_area("Enter Public Holidays (YYYY-MM-DD):", "Enter one date per line, e.g.:\n2023-01-01\n2023-12-25").strip().split("\n")
            st.session_state.public_holidays = []
            for date in public_holidays_input:
                if date.strip():
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

        if st.session_state.keywords_var:
            st.session_state.suspicious_keywords = st.text_area(
                "Enter Suspicious Keywords (comma-separated):",
                "miscellaneous, adjustment, correction, other, rounding"
            ).strip().split(",")
            st.session_state.suspicious_keywords = [keyword.strip().lower() for keyword in st.session_state.suspicious_keywords if keyword.strip()]

        if st.session_state.seldomly_used_accounts_var:
            st.session_state.seldomly_used_accounts_threshold = st.number_input(
                "Enter Threshold for Seldomly Used Accounts (minimum number of transactions):",
                value=5, min_value=1
            )

        if st.button("Run High-Risk Test"):
            perform_high_risk_test()
            visualize_high_risk_entries()

    # Export Reports
    st.header("5. Export Reports")
    if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
        if st.button("Export PDF Report"):
            pdf_output = export_pdf_report()
            st.download_button(
                label="Download PDF Report",
                data=pdf_output,
                file_name="audit_report.pdf",
                mime="application/pdf",
            )

        if st.button("Export Excel Report"):
            excel_output = export_excel_report()
            st.download_button(
                label="Download Excel Report",
                data=excel_output,
                file_name="flagged_entries.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Guide
    st.sidebar.header("Guide")
    st.sidebar.markdown("""
    **Journal Entry Testing Guide**

    The following fields are GL required for testing:
    - Transaction ID
    - Date
    - Debit Amount (Dr)
    - Credit Amount (Cr)
    - Account Number

    The following fields are TB required for testing:
    - Account Number
    - Opening Balance
    - Ending Balance

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
