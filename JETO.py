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
from pyxlsb import open_workbook  # For reading .xlsb files

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
if 'day_lag_threshold' not in st.session_state:
    st.session_state.day_lag_threshold = 7  # Default threshold for day lag

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

# Function to convert data types
def convert_data_types(df):
    numeric_fields = ["Debit Amount (Dr)", "Credit Amount (Cr)"]
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    date_fields = ["Date", "Posting Date"]
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors="coerce")
    return df

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
        st.warning("Completeness check has not passed. Please ensure the completeness check is successful before running high-risk tests.")
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

            rounded_entries = st.session_state.processed_df[
                st.session_state.processed_df["Debit Amount (Dr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold)) |
                st.session_state.processed_df["Credit Amount (Cr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold))
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, rounded_entries])
            st.session_state.flagged_entries_by_category["Rounded Numbers"] = rounded_entries

        if st.session_state.unusual_users_var:
            if "Created By" in st.session_state.processed_df.columns:
                if not st.session_state.authorized_users:
                    st.warning("No authorized users provided. Skipping unusual users check.")
                else:
                    unusual_user_entries = st.session_state.processed_df[~st.session_state.processed_df["Created By"].isin(st.session_state.authorized_users)]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, unusual_user_entries])
                    st.session_state.flagged_entries_by_category["Unauthorized Users"] = unusual_user_entries
            else:
                st.error("Column 'Created By' not found in the data.")
                return

        if st.session_state.post_closing_var:
            if "Date" in st.session_state.processed_df.columns:
                if st.session_state.closing_date is None:
                    st.warning("No closing date provided. Skipping post-closing entries check.")
                else:
                    post_closing_entries = st.session_state.processed_df[st.session_state.processed_df["Date"] > st.session_state.closing_date]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, post_closing_entries])
                    st.session_state.flagged_entries_by_category["Post-Closing Entries"] = post_closing_entries
            else:
                st.error("Column 'Date' not found in the data.")
                return

        if st.session_state.auth_threshold_var:
            threshold = st.session_state.auth_threshold
            below_threshold_entries = st.session_state.processed_df[
                (st.session_state.processed_df["Debit Amount (Dr)"] >= threshold * 0.9) & 
                (st.session_state.processed_df["Debit Amount (Dr)"] < threshold) |
                (st.session_state.processed_df["Credit Amount (Cr)"] >= threshold * 0.9) & 
                (st.session_state.processed_df["Credit Amount (Cr)"] < threshold)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, below_threshold_entries])
            st.session_state.flagged_entries_by_category["Below Authorization Threshold"] = below_threshold_entries

        if st.session_state.nine_pattern_var:
            nine_pattern_entries = st.session_state.processed_df[
                st.session_state.processed_df["Debit Amount (Dr)"].apply(is_99999) |
                st.session_state.processed_df["Credit Amount (Cr)"].apply(is_99999)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, nine_pattern_entries])
            st.session_state.flagged_entries_by_category["99999 Pattern"] = nine_pattern_entries

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
                    st.session_state.flagged_entries_by_category["Suspicious Keywords"] = keyword_entries
            else:
                st.error("Column 'Entry Description' not found in the data.")
                return

        if st.session_state.seldomly_used_accounts_var:
            if st.session_state.processed_df is not None:
                account_frequency = st.session_state.processed_df["Account Number"].value_counts().reset_index()
                account_frequency.columns = ["Account Number", "Transaction Count"]
                seldomly_used_accounts = account_frequency[account_frequency["Transaction Count"] < st.session_state.seldomly_used_accounts_threshold]
                seldomly_used_entries = st.session_state.processed_df[
                    st.session_state.processed_df["Account Number"].isin(seldomly_used_accounts["Account Number"])
                ]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, seldomly_used_entries])
                st.session_state.flagged_entries_by_category["Seldomly Used Accounts"] = seldomly_used_entries

        # Day Laps or Lag High-Risk Criterion
        if st.session_state.day_lag_var:
            if "Date" in st.session_state.processed_df.columns and "Posting Date" in st.session_state.processed_df.columns:
                st.session_state.processed_df["Day Lag"] = (st.session_state.processed_df["Posting Date"] - st.session_state.processed_df["Date"]).dt.days
                day_lag_entries = st.session_state.processed_df[st.session_state.processed_df["Day Lag"] > st.session_state.day_lag_threshold]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, day_lag_entries])
                st.session_state.flagged_entries_by_category["Day Lag"] = day_lag_entries
            else:
                st.error("Columns 'Date' and 'Posting Date' are required for day lag analysis.")

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
        if username == "m.elansary@maham.com" and password == "74107410":
            st.session_state.logged_in = True
            st.session_state.logged_in_user = username
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='footer'>Developed by Innovation and Transformation Team: Mahmoud Elansary and Sabeeh Uddin</div>", unsafe_allow_html=True)

# Streamlit UI
def main_app():
    st.title("MAHx-JET - Maham for Professional Services")

    # Data Import & Processing
    st.header("1. Data Import & Processing")
    uploaded_file = st.file_uploader("Import GL Dump File", type=["csv", "xlsx", "xlsb", "txt"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                # Read CSV in chunks for large files
                chunks = pd.read_csv(uploaded_file, chunksize=100000)
                st.session_state.df = pd.concat(chunks, ignore_index=True)
            elif uploaded_file.name.endswith('.xlsx'):
                st.session_state.df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.xlsb'):
                with open_workbook(uploaded_file) as wb:
                    with wb.get_sheet(1) as sheet:
                        data = []
                        for row in sheet.rows():
                            data.append([item.v for item in row])
                        st.session_state.df = pd.DataFrame(data[1:], columns=data[0])
            elif uploaded_file.name.endswith('.txt'):
                st.session_state.df = pd.read_csv(uploaded_file, delimiter='\t')
            st.success("File imported successfully!")
        except Exception as e:
            st.error(f"Failed to import file: {e}")
            logging.error(f"Failed to import file: {e}")

    # Import Trial Balance
    st.subheader("Import Trial Balance")
    tb_uploaded_file = st.file_uploader("Import Trial Balance File", type=["csv", "xlsx", "xlsb", "txt"])
    if tb_uploaded_file is not None:
        try:
            if tb_uploaded_file.name.endswith('.csv'):
                st.session_state.trial_balance = pd.read_csv(tb_uploaded_file)
            elif tb_uploaded_file.name.endswith('.xlsx'):
                st.session_state.trial_balance = pd.read_excel(tb_uploaded_file)
            elif tb_uploaded_file.name.endswith('.xlsb'):
                with open_workbook(tb_uploaded_file) as wb:
                    with wb.get_sheet(1) as sheet:
                        data = []
                        for row in sheet.rows():
                            data.append([item.v for item in row])
                        st.session_state.trial_balance = pd.DataFrame(data[1:], columns=data[0])
            elif tb_uploaded_file.name.endswith('.txt'):
                st.session_state.trial_balance = pd.read_csv(tb_uploaded_file, delimiter='\t')
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
        st.session_state.day_lag_var = st.checkbox("Day Laps or Lag")

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

        if st.session_state.day_lag_var:
            st.session_state.day_lag_threshold = st.number_input(
                "Enter Threshold for Day Lag (maximum allowed days between creation and posting):",
                value=7, min_value=1
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

    The following fields are required for testing:
    - Transaction ID
    - Date
    - Debit Amount (Dr)
    - Credit Amount (Cr)
    - Account Number

    **Steps:**
    1. Import a file containing the required fields.
    2. Map the columns to the required fields.
    3. Set high-risk criteria (e.g., public holidays, rounded numbers, unusual users, post-closing entries).
    4. Run the test to identify high-risk entries.
    5. Export the results to a file.
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
