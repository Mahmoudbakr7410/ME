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
from functools import lru_cache
import calendar

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
if 'delimiter' not in st.session_state:
    st.session_state.delimiter = None
if 'public_holidays_var' not in st.session_state:
    st.session_state.public_holidays_var = False
if 'suspicious_keywords_var' not in st.session_state:
    st.session_state.suspicious_keywords_var = False
if 'rounded_numbers_var' not in st.session_state:
    st.session_state.rounded_numbers_var = False
if 'weekend_transactions_var' not in st.session_state:
    st.session_state.weekend_transactions_var = False
if 'seldomly_used_accounts' not in st.session_state:
    st.session_state.seldomly_used_accounts = pd.DataFrame()
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

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

# Function to load data
def load_data(uploaded_file, delimiter):
    try:
        df = pd.read_csv(uploaded_file, delimiter=delimiter, encoding='utf-8', on_bad_lines='skip')
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

# Function to load trial balance data
def load_trial_balance(uploaded_file, delimiter):
    try:
        trial_balance = pd.read_csv(uploaded_file, delimiter=delimiter, encoding='utf-8', on_bad_lines='skip')
        return trial_balance
    except Exception as e:
        st.error(f"Error reading trial balance file: {e}")
        return None

# Function to ensure required columns are present and filled
def check_required_columns(df):
    missing_columns = [field for field in required_fields if field not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return False

    empty_columns = [field for field in required_fields if field in df.columns and df[field].isnull().all()]
    if empty_columns:
        st.error(f"Required columns are completely empty: {', '.join(empty_columns)}")
        return False

    return True

# Function to add public holidays based on the selected country and year
def add_public_holidays(year, country="Saudi Arabia"):
    holidays = []
    if country == "Saudi Arabia":
        # Define public holidays for Saudi Arabia
        holidays.extend([
            f"{year}-09-23",  # Saudi National Day
            f"{year}-04-10",  # Eid al-Fitr (approximate)
            f"{year}-06-16"   # Eid al-Adha (approximate)
        ])
    elif country == "United States":
        # Define public holidays for the United States
        holidays.extend([
            f"{year}-01-01",  # New Year's Day
            f"{year}-07-04",  # Independence Day
            f"{year}-12-25"   # Christmas Day
        ])
    else:
        st.warning("No specific public holidays defined for the selected country.")

    # Convert the list of holiday dates to datetime objects
    holiday_dates = pd.to_datetime(holidays, errors='coerce')
    return holiday_dates.dropna().tolist()

# Function to check for 99999 pattern
def is_99999(value):
    try:
        value = float(value)
        return abs(value - round(value, 0)) >= 0.999 and abs(value - round(value, 0)) < 1.0
    except (ValueError, TypeError):
        return False

# Function to perform completeness check
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

# Function to detect seldomly used accounts
def detect_seldomly_used_accounts():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to analyze. Please import a file first.")
        return

    try:
        account_frequency = st.session_state.processed_df["Account Number"].value_counts().reset_index()
        account_frequency.columns = ["Account Number", "Transaction Count"]
        seldomly_used_accounts = account_frequency[account_frequency["Transaction Count"] < st.session_state.seldomly_used_accounts_threshold]
        st.session_state.seldomly_used_accounts = seldomly_used_accounts
        st.subheader("Seldomly Used Accounts")
        st.write(f"Found {len(seldomly_used_accounts)} accounts with fewer than {st.session_state.seldomly_used_accounts_threshold} transactions.")
        st.dataframe(seldomly_used_accounts)
        st.subheader("Conclusion")
        if len(seldomly_used_accounts) > 0:
            st.warning(f"{len(seldomly_used_accounts)} accounts are seldomly used. Review these accounts for potential risks.")
        else:
            st.success("No seldomly used accounts found.")
    except Exception as e:
        st.error(f"Error during seldomly used accounts detection: {e}")
        logging.error(f"Error during seldomly used accounts detection: {e}")

# Function to perform data mining and pattern recognition
def perform_pattern_recognition():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to analyze. Please import a file first.")
        return

    try:
        numeric_cols = st.session_state.processed_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            st.warning("No numeric columns found for pattern recognition.")
            return
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(st.session_state.processed_df[numeric_cols])
        kmeans = KMeans(n_clusters=3)
        clusters = kmeans.fit_predict(scaled_data)
        st.session_state.processed_df["Cluster"] = clusters
        cluster_summary = st.session_state.processed_df.groupby("Cluster").agg(
            Count=("Cluster", "size"),
            Avg_Debit=("Debit Amount (Dr)", "mean"),
            Avg_Credit=("Credit Amount (Cr)", "mean")
        ).reset_index()
        st.session_state.pattern_recognition_results = cluster_summary
        st.subheader("Pattern Recognition Results")
        st.dataframe(cluster_summary)
        st.subheader("Conclusion")
        if len(cluster_summary) > 1:
            st.success("Pattern recognition identified distinct groups of transactions. Review the clusters for insights.")
        else:
            st.warning("No significant patterns were found in the data.")
    except Exception as e:
        st.error(f"Error during pattern recognition: {e}")
        logging.error(f"Error during pattern recognition: {e}")

# Function to export PDF report
def export_pdf_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Maham for Professional Services", ln=True, align="C")
    pdf.cell(200, 10, txt=f"Audited Client: {st.session_state.audited_client_name}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Year Audited: {st.session_state.year_audited}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Report Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Generated By: {st.session_state.logged_in_user}", ln=True, align="L")
    pdf.cell(200, 10, txt="Completeness Check Conclusion:", ln=True, align="L")
    if st.session_state.completeness_check_passed:
        pdf.cell(200, 10, txt="Completeness check passed. Maximum discrepancy is within the allowed tolerance of 5.", ln=True, align="L")
    else:
        max_discrepancy = st.session_state.completeness_check_results["Discrepancy"].abs().max()
        pdf.cell(200, 10, txt=f"Completeness check failed. Maximum discrepancy ({max_discrepancy}) exceeds the allowed tolerance of 5.", ln=True, align="L")
    pdf.cell(200, 10, txt="Flagged Entries by Category:", ln=True, align="L")
    pdf.set_font("Arial", size=10)
    for category, entries in st.session_state.flagged_entries_by_category.items():
        pdf.cell(200, 10, txt=f"Category: {category}", ln=True, align="L")
        for index, row in entries.iterrows():
            pdf.cell(200, 10, txt=f"Transaction ID: {row['Transaction ID']}, Date: {row['Date']}, Debit: {row['Debit Amount (Dr)']}, Credit: {row['Credit Amount (Cr)']}", ln=True, align="L")
    pdf_output = pdf.output(dest="S").encode("latin1")
    return pdf_output

# Function to export Excel report
def export_excel_report():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for category, entries in st.session_state.flagged_entries_by_category.items():
            entries.to_excel(writer, sheet_name=category, index=False)
    output.seek(0)
    return output

# Function to perform high-risk testing
def perform_high_risk_test():
    if not st.session_state.completeness_check_passed:
        st.warning("High-risk tests are disabled until the completeness check passes with a maximum discrepancy of 5.")
        return

    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to test. Please import a file first.")
        return

    try:
        st.session_state.high_risk_entries = pd.DataFrame()
        st.session_state.flagged_entries_by_category = {}

        if st.session_state.public_holidays_var:
            if "Date" in st.session_state.processed_df.columns:
                holiday_entries = st.session_state.processed_df[st.session_state.processed_df["Date"].isin(st.session_state.public_holidays)]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, holiday_entries])
                st.session_state.flagged_entries_by_category["Public Holidays"] = holiday_entries
            else:
                st.warning("No 'Date' column found for public holiday testing.")

        if st.session_state.suspicious_keywords_var:
            description_column = "Entry Description"  # Adjust column name as needed
            if description_column in st.session_state.processed_df.columns:
                keyword_entries = st.session_state.processed_df[st.session_state.processed_df[description_column].str.contains('|'.join(st.session_state.suspicious_keywords), case=False, na=False)]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, keyword_entries])
                st.session_state.flagged_entries_by_category["Suspicious Keywords"] = keyword_entries
            else:
                st.warning(f"No '{description_column}' column found for keyword testing.")

        if st.session_state.rounded_numbers_var:
            rounded_entries = st.session_state.processed_df[st.session_state.processed_df.apply(lambda row: any(is_99999(row[col]) for col in ["Debit Amount (Dr)", "Credit Amount (Cr)"]), axis=1)]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, rounded_entries])
            st.session_state.flagged_entries_by_category["Rounded Numbers"] = rounded_entries

        if st.session_state.weekend_transactions_var:
            if "Date" in st.session_state.processed_df.columns:
                weekend_entries = st.session_state.processed_df[st.session_state.processed_df["Date"].dt.dayofweek.isin([5, 6])]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, weekend_entries])
                st.session_state.flagged_entries_by_category["Weekend Transactions"] = weekend_entries
            else:
                st.warning("No 'Date' column found for weekend transactions testing.")

        st.subheader("High-Risk Entries")
        if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
            st.dataframe(st.session_state.high_risk_entries)
        else:
            st.success("No high-risk entries found.")

        st.subheader("Flagged Entries by Category")
        for category, entries in st.session_state.flagged_entries_by_category.items():
            st.write(f"Category: {category}")
            if entries is not None and not entries.empty:
                st.dataframe(entries)
            else:
                st.write("No entries found in this category.")

    except Exception as e:
        st.error(f"Error during high-risk testing: {e}")
        logging.error(f"Error during high-risk testing: {e}")

# Streamlit app layout
def main():
    st.title("Internal Audit Tool")

    # Login section
    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in authorized_users and authorized_users[username] == password:
                st.success("Logged in successfully!")
                st.session_state.logged_in = True
                st.session_state.logged_in_user = username
            else:
                st.error("Incorrect username or password.")

    if st.session_state.logged_in:
        st.write(f"Welcome, {st.session_state.logged_in_user}!")

        # Sidebar for settings and inputs
        with st.sidebar:
            st.header("Settings")

            st.session_state.audited_client_name = st.text_input("Audited Client Name", value=st.session_state.audited_client_name)
            st.session_state.year_audited = st.number_input("Year Audited", min_value=2000, max_value=datetime.now().year, value=st.session_state.year_audited)

            st.session_state.seldomly_used_accounts_threshold = st.number_input("Seldomly Used Accounts Threshold", min_value=1, value=st.session_state.seldomly_used_accounts_threshold)

            st.session_state.auth_threshold = st.number_input("Authorization Threshold", min_value=1, value=st.session_state.auth_threshold)

            uploaded_file = st.file_uploader("Upload GL Data (CSV/TXT)", type=["csv", "txt"])

            if uploaded_file is not None:
                st.session_state.delimiter = st.text_input("Enter delimiter (e.g., ',', ';')", value=",")

                if st.session_state.delimiter:
                    try:
                        st.session_state.df = load_data(uploaded_file, st.session_state.delimiter)
                        if st.session_state.df is not None:
                            st.success("GL Data loaded successfully!")
                    except Exception as e:
                        st.error(f"Error loading data: {e}")

            trial_balance_file = st.file_uploader("Upload Trial Balance (CSV/TXT)", type=["csv", "txt"])

            if trial_balance_file is not None:
                trial_delimiter = st.text_input("Enter Trial Balance delimiter (e.g., ',', ';')", value=",")
                if trial_delimiter:
                    try:
                        st.session_state.trial_balance = load_trial_balance(trial_balance_file, trial_delimiter)
                        if st.session_state.trial_balance is not None:
                            st.success("Trial Balance loaded successfully!")
                    except Exception as e:
                        st.error(f"Error loading trial balance: {e}")

            st.session_state.public_holidays_var = st.checkbox("Include Public Holidays", value=False)
            if st.session_state.public_holidays_var:
                st.session_state.public_holidays = add_public_holidays(st.session_state.year_audited)
                st.write("Public Holidays:", st.session_state.public_holidays)

            st.session_state.suspicious_keywords_var = st.checkbox("Include Suspicious Keywords", value=False)
            if st.session_state.suspicious_keywords_var:
                keywords_input = st.text_input("Enter suspicious keywords (comma-separated)", value="fraud, scam")
                st.session_state.suspicious_keywords = [keyword.strip() for keyword in keywords_input.split(',')]

            st.session_state.rounded_numbers_var = st.checkbox("Include Rounded Numbers (99999)", value=False)
            st.session_state.weekend_transactions_var = st.checkbox("Include Weekend Transactions", value=False)

        # Main section for data display and analysis
        if st.session_state.df is not None:
            st.subheader("Uploaded GL Data")
            st.dataframe(st.session_state.df.head())

            if check_required_columns(st.session_state.df):
                st.session_state.processed_df = convert_data_types(st.session_state.df.copy())

                st.subheader("Analysis Options")
                if st.button("Run Completeness Check"):
                    perform_completeness_check()

                if st.button("Detect Seldomly Used Accounts"):
                    detect_seldomly_used_accounts()

                if st.button("Perform Pattern Recognition"):
                    perform_pattern_recognition()

                if st.button("Run High-Risk Tests"):
                    perform_high_risk_test()

                if st.session_state.flagged_entries_by_category:
                    st.subheader("Export Options")
                    if st.download_button("Export Flagged Entries to Excel", data=export_excel_report(), file_name="flagged_entries.xlsx"):
                        st.success("Excel report generated!")

                    if st.download_button("Export Report to PDF", data=export_pdf_report(), file_name="audit_report.pdf"):
                        st.success("PDF report generated!")

# Run the app
if __name__ == "__main__":
    main()
