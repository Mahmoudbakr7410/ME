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
import pyodbc  # For SQL Azure connection

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

# Function to connect to SQL Azure
def get_db_connection():
    server = "mahx.database.windows.net"
    database = "MAHx"
    username = "mahmoudbakr7410@gmail.com@mahx"
    password = "7oda@ELBASHA"
    driver = '{ODBC Driver 17 for SQL Server}'
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(connection_string)
    return conn

# Function to store data in SQL Azure
def store_data_to_sql(df, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create a temporary table to store the data
    cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
    
    # Create the table with the appropriate schema
    columns = df.columns
    columns_with_types = ", ".join([f"{col} NVARCHAR(MAX)" for col in columns])
    cursor.execute(f"CREATE TABLE {table_name} ({columns_with_types});")
    
    # Insert data into the table
    for _, row in df.iterrows():
        values = ", ".join([f"'{str(value)}'" for value in row.values])
        cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({values});")
    
    conn.commit()
    conn.close()

# Function to fetch data from SQL Azure
def fetch_data_from_sql(table_name):
    conn = get_db_connection()
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Function to detect delimiter for txt files
def detect_delimiter(file):
    sample = file.read(1024).decode('utf-8')
    file.seek(0)
    sniffer = csv.Sniffer()
    delimiter = sniffer.sniff(sample).delimiter
    return delimiter

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

# Function to perform completeness check
def perform_completeness_check(processed_df, trial_balance_df):
    try:
        gl_summary = processed_df.groupby("Account Number").agg(
            Total_Debits=("Debit Amount (Dr)", "sum"),
            Total_Credits=("Credit Amount (Cr)", "sum")
        ).reset_index()
        merged_df = pd.merge(
            trial_balance_df,
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

# Function to perform high-risk testing
def perform_high_risk_test(processed_df):
    try:
        st.session_state.high_risk_entries = pd.DataFrame()
        st.session_state.flagged_entries_by_category = {}

        if st.session_state.public_holidays_var:
            if "Date" in processed_df.columns:
                holiday_entries = processed_df[processed_df["Date"].isin(st.session_state.public_holidays)]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, holiday_entries])
                st.session_state.flagged_entries_by_category["Public Holidays"] = holiday_entries
            else:
                st.error("Column 'Date' not found in the data.")
                return

        if st.session_state.rounded_var:
            def is_rounded(value, threshold):
                try:
                    value = float(value)
                    if value == 0:
                        return False
                    return (value % threshold == 0) or (math.isclose(value % threshold, threshold, rel_tol=1e-6))
                except (ValueError, TypeError):
                    return False

            rounded_entries = processed_df[
                processed_df["Debit Amount (Dr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold)) |
                processed_df["Credit Amount (Cr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold))
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, rounded_entries])
            st.session_state.flagged_entries_by_category["Rounded Numbers"] = rounded_entries

        if st.session_state.unusual_users_var:
            if "Created By" in processed_df.columns:
                if not st.session_state.authorized_users:
                    st.warning("No authorized users provided. Skipping unusual users check.")
                else:
                    unusual_user_entries = processed_df[~processed_df["Created By"].isin(st.session_state.authorized_users)]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, unusual_user_entries])
                    st.session_state.flagged_entries_by_category["Unauthorized Users"] = unusual_user_entries
            else:
                st.error("Column 'Created By' not found in the data.")
                return

        if st.session_state.post_closing_var:
            if "Date" in processed_df.columns:
                if st.session_state.closing_date is None:
                    st.warning("No closing date provided. Skipping post-closing entries check.")
                else:
                    closing_date = pd.to_datetime(st.session_state.closing_date)
                    processed_df["Date"] = pd.to_datetime(processed_df["Date"])
                    audited_year_end = pd.to_datetime(f"{st.session_state.year_audited}-12-31")
                    if closing_date <= audited_year_end:
                        st.error("Closing date must be after the audited year's December 31.")
                        return
                    post_closing_entries = processed_df[processed_df["Date"] > closing_date]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, post_closing_entries])
                    st.session_state.flagged_entries_by_category["Post-Closing Entries"] = post_closing_entries
            else:
                st.error("Column 'Date' not found in the data.")
                return

        if st.session_state.auth_threshold_var:
            threshold = st.session_state.auth_threshold
            below_threshold_entries = processed_df[
                (processed_df["Debit Amount (Dr)"] >= threshold * 0.9) & 
                (processed_df["Debit Amount (Dr)"] < threshold) |
                (processed_df["Credit Amount (Cr)"] >= threshold * 0.9) & 
                (processed_df["Credit Amount (Cr)"] < threshold)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, below_threshold_entries])
            st.session_state.flagged_entries_by_category["Below Authorization Threshold"] = below_threshold_entries

        if st.session_state.nine_pattern_var:
            nine_pattern_entries = processed_df[
                processed_df["Debit Amount (Dr)"].apply(is_99999) |
                processed_df["Credit Amount (Cr)"].apply(is_99999)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, nine_pattern_entries])
            st.session_state.flagged_entries_by_category["99999 Pattern"] = nine_pattern_entries

        if st.session_state.keywords_var:
            if "Entry Description" in processed_df.columns:
                if not st.session_state.suspicious_keywords:
                    st.warning("No suspicious keywords provided. Skipping keyword check.")
                else:
                    keyword_entries = processed_df[
                        processed_df["Entry Description"].str.contains(
                            "|".join(st.session_state.suspicious_keywords), case=False, na=False
                        )
                    ]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, keyword_entries])
                    st.session_state.flagged_entries_by_category["Suspicious Keywords"] = keyword_entries
            else:
                st.error("Column 'Entry Description' not found in the data.")
                return

        if st.session_state.seldomly_used_accounts_var:
            if processed_df is not None:
                account_frequency = processed_df["Account Number"].value_counts().reset_index()
                account_frequency.columns = ["Account Number", "Transaction Count"]
                seldomly_used_accounts = account_frequency[account_frequency["Transaction Count"] < st.session_state.seldomly_used_accounts_threshold]
                seldomly_used_entries = processed_df[
                    processed_df["Account Number"].isin(seldomly_used_accounts["Account Number"])
                ]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, seldomly_used_entries])
                st.session_state.flagged_entries_by_category["Seldomly Used Accounts"] = seldomly_used_entries

        if not st.session_state.high_risk_entries.empty:
            st.success(f"Found {len(st.session_state.high_risk_entries)} high-risk entries.")
        else:
            st.success("No high-risk entries found.")
    except Exception as e:
        st.error(f"Error during testing: {e}")
        logging.error(f"Error during high-risk testing: {e}")

# Function to visualize high-risk entries
def visualize_high_risk_entries():
    if not st.session_state.high_risk_entries.empty:
        st.header("High-Risk Entries Visualization")

        # Bar chart for counts of high-risk entries by category
        st.subheader("Count of High-Risk Entries by Category")
        category_counts = {category: len(entries) for category, entries in st.session_state.flagged_entries_by_category.items()}
        fig = px.bar(x=list(category_counts.keys()), y=list(category_counts.values()), labels={"x": "Category", "y": "Count"})
        st.plotly_chart(fig)

        # Pie chart for distribution of high-risk entries
        st.subheader("Distribution of High-Risk Entries")
        fig = px.pie(names=list(category_counts.keys()), values=list(category_counts.values()))
        st.plotly_chart(fig)

        # Scatter plot for rounded numbers
        if "Rounded Numbers" in st.session_state.flagged_entries_by_category:
            st.subheader("Rounded Numbers Scatter Plot")
            rounded_entries = st.session_state.flagged_entries_by_category["Rounded Numbers"]
            fig = px.scatter(rounded_entries, x="Debit Amount (Dr)", y="Credit Amount (Cr)", color="Account Number")
            st.plotly_chart(fig)

        # Scatter plot for 99999 pattern
        if "99999 Pattern" in st.session_state.flagged_entries_by_category:
            st.subheader("99999 Pattern Scatter Plot")
            nine_pattern_entries = st.session_state.flagged_entries_by_category["99999 Pattern"]
            fig = px.scatter(nine_pattern_entries, x="Debit Amount (Dr)", y="Credit Amount (Cr)", color="Account Number")
            st.plotly_chart(fig)

# Authentication
def login():
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

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://res.cloudinary.com/dwtw5d4kq/image/upload/v1740139683/cropped-oie_NfAWRTRKjjnC-1_c8my9c.png", width=50)
    with col2:
        st.markdown("<h2 style='text-align: left;'>Maham Data Analyzer</h2>", unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<h2>Login</h2>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in authorized_users and authorized_users[username] == password:
            st.session_state.logged_in = True
            st.session_state.logged_in_user = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='footer'>Developed by Innovation and Transformation Team: Mahmoud Elansary and Sabeeh Uddin</div>", unsafe_allow_html=True)

# Streamlit UI
def main_app():
    st.title("MAHAM DATA DEEP ANALYZER DEMO")

    # Data Import & Processing
    st.header("1. Data Import & Processing")
    
    # Upload GL Data
    uploaded_file = st.file_uploader("Upload GL Data (CSV or Excel)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            st.session_state.df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            st.session_state.df = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully!")

    # Upload Trial Balance
    uploaded_trial_balance = st.file_uploader("Upload Trial Balance (CSV or Excel)", type=["csv", "xlsx"])
    if uploaded_trial_balance is not None:
        if uploaded_trial_balance.name.endswith(".csv"):
            st.session_state.trial_balance = pd.read_csv(uploaded_trial_balance)
        elif uploaded_trial_balance.name.endswith(".xlsx"):
            st.session_state.trial_balance = pd.read_excel(uploaded_trial_balance)
        st.success("Trial Balance uploaded successfully!")

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
                processed_df = st.session_state.df.rename(columns={v: k for k, v in st.session_state.column_mapping.items() if v != ""})
                processed_df = convert_data_types(processed_df)
                store_data_to_sql(processed_df, "Processed_Data")  # Store processed data in SQL Azure
                st.success("Columns mapped and data stored successfully!")

    # Completeness Check
    st.header("2. Completeness Check")
    if st.button("Run Completeness Check"):
        processed_df = fetch_data_from_sql("Processed_Data")
        trial_balance_df = fetch_data_from_sql("Trial_Balance")
        
        if processed_df is not None and trial_balance_df is not None:
            perform_completeness_check(processed_df, trial_balance_df)
        else:
            st.warning("No data to test. Please import and process data first.")

    # Data Mining and Pattern Recognition
    st.header("3. Data Mining and Pattern Recognition")
    if st.button("Run Pattern Recognition"):
        processed_df = fetch_data_from_sql("Processed_Data")
        if processed_df is not None:
            perform_pattern_recognition(processed_df)
        else:
            st.warning("No data to analyze. Please import and process data first.")

    # High-Risk Criteria & Testing
    st.header("4. High-Risk Criteria & Testing")
    if st.button("Run High-Risk Test"):
        processed_df = fetch_data_from_sql("Processed_Data")
        if processed_df is not None:
            perform_high_risk_test(processed_df)
            visualize_high_risk_entries()
        else:
            st.warning("No data to test. Please import and process data first.")

    # Export Reports
    st.header("5. Export Reports")
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
    processed_df = fetch_data_from_sql("Processed_Data")
    if processed_df is not None and not processed_df.empty:
        st.header("Preview Data")
        st.dataframe(processed_df.head(10))

# Check if user is logged in
if not st.session_state.logged_in:
    login()
else:
    main_app()
