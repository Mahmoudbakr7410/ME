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
if 'pattern_recognition_results' not in st.session_state:  # New session state variable for pattern recognition
    st.session_state.pattern_recognition_results = None
if 'seldomly_used_accounts_threshold' not in st.session_state:  # New session state variable for seldomly used accounts threshold
    st.session_state.seldomly_used_accounts_threshold = 5
if 'monthly_trial_balance' not in st.session_state:  # New session state variable for monthly trial balance
    st.session_state.monthly_trial_balance = None

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

# Function to perform completeness check
def perform_completeness_check():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No GL data to test. Please import a CSV file first.")
        return
    if st.session_state.trial_balance is None or st.session_state.trial_balance.empty:
        st.warning("No trial balance data to test. Please import a trial balance CSV file first.")
        return

    try:
        # Group GL data by account number and calculate total debits and credits
        gl_summary = st.session_state.processed_df.groupby("Account Number").agg(
            Total_Debits=("Debit Amount (Dr)", "sum"),
            Total_Credits=("Credit Amount (Cr)", "sum")
        ).reset_index()

        # Merge GL summary with trial balance
        merged_df = pd.merge(
            st.session_state.trial_balance,
            gl_summary,
            on="Account Number",
            how="left"
        )

        # Fill NaN values with 0 (in case some accounts have no transactions)
        merged_df["Total_Debits"] = merged_df["Total_Debits"].fillna(0)
        merged_df["Total_Credits"] = merged_df["Total_Credits"].fillna(0)

        # Calculate expected ending balance
        merged_df["Expected_Ending_Balance"] = (
            merged_df["Opening Balance"] + merged_df["Total_Debits"] - merged_df["Total_Credits"]
        )

        # Compare expected vs actual ending balance
        merged_df["Discrepancy"] = (
            merged_df["Expected_Ending_Balance"] - merged_df["Ending Balance"]
        )

        # Store results in session state
        st.session_state.completeness_check_results = merged_df

        # Check if discrepancies are within the allowed tolerance (5)
        max_discrepancy = merged_df["Discrepancy"].abs().max()
        if max_discrepancy <= 5:
            st.session_state.completeness_check_passed = True
            st.success("Completeness check passed! Maximum discrepancy is within the allowed tolerance of 5.")
        else:
            st.session_state.completeness_check_passed = False
            st.warning(f"Completeness check failed! Maximum discrepancy ({max_discrepancy}) exceeds the allowed tolerance of 5.")

        # Display results
        st.dataframe(merged_df)

        # Flag accounts with discrepancies
        discrepancies = merged_df[abs(merged_df["Discrepancy"]) > 0.01]  # Tolerance of 0.01 for rounding errors
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
        st.warning("No data to analyze. Please import a CSV file first.")
        return

    try:
        # Count the frequency of each account number
        account_frequency = st.session_state.processed_df["Account Number"].value_counts().reset_index()
        account_frequency.columns = ["Account Number", "Transaction Count"]

        # Define seldomly used accounts as those with fewer than the specified threshold
        seldomly_used_accounts = account_frequency[account_frequency["Transaction Count"] < st.session_state.seldomly_used_accounts_threshold]

        # Store results in session state
        st.session_state.seldomly_used_accounts = seldomly_used_accounts

        # Display results
        st.subheader("Seldomly Used Accounts")
        st.write(f"Found {len(seldomly_used_accounts)} accounts with fewer than {st.session_state.seldomly_used_accounts_threshold} transactions.")
        st.dataframe(seldomly_used_accounts)

        # Provide a conclusion
        st.subheader("Conclusion")
        if len(seldomly_used_accounts) > 0:
            st.warning(f"{len(seldomly_used_accounts)} accounts are seldomly used. Review these accounts for potential risks.")
        else:
            st.success("No seldomly used accounts found.")
    except Exception as e:
        st.error(f"Error during seldomly used accounts detection: {e}")
        logging.error(f"Error during seldomly used accounts detection: {e}")

# Function to create monthly trial balance
def create_monthly_trial_balance():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to analyze. Please import a CSV file first.")
        return

    try:
        # Extract month and year from the Date column
        st.session_state.processed_df["Month"] = st.session_state.processed_df["Date"].dt.to_period("M")

        # Group by Account Number and Month, then calculate total debits and credits
        monthly_trial_balance = st.session_state.processed_df.groupby(["Account Number", "Month"]).agg(
            Total_Debits=("Debit Amount (Dr)", "sum"),
            Total_Credits=("Credit Amount (Cr)", "sum")
        ).reset_index()

        # Calculate the net balance for each account per month
        monthly_trial_balance["Net Balance"] = monthly_trial_balance["Total_Debits"] - monthly_trial_balance["Total_Credits"]

        # Store results in session state
        st.session_state.monthly_trial_balance = monthly_trial_balance

        # Display results
        st.subheader("Monthly Trial Balance")
        st.dataframe(monthly_trial_balance)

        # Provide a conclusion
        st.subheader("Conclusion")
        st.success("Monthly trial balance created successfully!")
    except Exception as e:
        st.error(f"Error during monthly trial balance creation: {e}")
        logging.error(f"Error during monthly trial balance creation: {e}")

# Function to perform data mining and pattern recognition
def perform_pattern_recognition():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to analyze. Please import a CSV file first.")
        return

    try:
        # Select numeric columns for pattern recognition
        numeric_cols = st.session_state.processed_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            st.warning("No numeric columns found for pattern recognition.")
            return

        # Scale the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(st.session_state.processed_df[numeric_cols])

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=3)  # You can adjust the number of clusters
        clusters = kmeans.fit_predict(scaled_data)

        # Add cluster results to the dataframe
        st.session_state.processed_df["Cluster"] = clusters

        # Analyze clusters for patterns
        cluster_summary = st.session_state.processed_df.groupby("Cluster").agg(
            Count=("Cluster", "size"),
            Avg_Debit=("Debit Amount (Dr)", "mean"),
            Avg_Credit=("Credit Amount (Cr)", "mean")
        ).reset_index()

        # Store results in session state
        st.session_state.pattern_recognition_results = cluster_summary

        # Display results
        st.subheader("Pattern Recognition Results")
        st.dataframe(cluster_summary)

        # Provide a conclusion based on the clusters
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

    # Add firm name
    pdf.cell(200, 10, txt="Maham for Professional Services", ln=True, align="C")

    # Add audited client name and year
    pdf.cell(200, 10, txt=f"Audited Client: {st.session_state.audited_client_name}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Year Audited: {st.session_state.year_audited}", ln=True, align="L")

    # Add timing and username
    pdf.cell(200, 10, txt=f"Report Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Generated By: {st.session_state.logged_in_user}", ln=True, align="L")

    # Add completeness check conclusion
    pdf.cell(200, 10, txt="Completeness Check Conclusion:", ln=True, align="L")
    if st.session_state.completeness_check_passed:
        pdf.cell(200, 10, txt="Completeness check passed. Maximum discrepancy is within the allowed tolerance of 5.", ln=True, align="L")
    else:
        max_discrepancy = st.session_state.completeness_check_results["Discrepancy"].abs().max()
        pdf.cell(200, 10, txt=f"Completeness check failed. Maximum discrepancy ({max_discrepancy}) exceeds the allowed tolerance of 5.", ln=True, align="L")

    # Add flagged entries by category
    pdf.cell(200, 10, txt="Flagged Entries by Category:", ln=True, align="L")
    pdf.set_font("Arial", size=10)
    for category, entries in st.session_state.flagged_entries_by_category.items():
        pdf.cell(200, 10, txt=f"Category: {category}", ln=True, align="L")
        for index, row in entries.iterrows():
            pdf.cell(200, 10, txt=f"Transaction ID: {row['Transaction ID']}, Date: {row['Date']}, Debit: {row['Debit Amount (Dr)']}, Credit: {row['Credit Amount (Cr)']}", ln=True, align="L")

    # Save the PDF
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
        st.warning("No data to test. Please import a CSV file first.")
        return

    try:
        # Initialize high-risk entries
        st.session_state.high_risk_entries = pd.DataFrame()
        st.session_state.flagged_entries_by_category = {}  # Reset flagged entries by category

        # Check for public holiday entries
        if st.session_state.public_holidays_var:
            if "Date" in st.session_state.processed_df.columns:
                holiday_entries = st.session_state.processed_df[st.session_state.processed_df["Date"].isin(st.session_state.public_holidays)]
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, holiday_entries])
                st.session_state.flagged_entries_by_category["Public Holidays"] = holiday_entries
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
            st.session_state.flagged_entries_by_category["Rounded Numbers"] = rounded_entries

        # Check for unusual users
        if st.session_state.unusual_users_var:
            if "Created By" in st.session_state.processed_df.columns:
                # Ensure authorized_users is not empty
                if not st.session_state.authorized_users:
                    st.warning("No authorized users provided. Skipping unusual users check.")
                else:
                    unusual_user_entries = st.session_state.processed_df[~st.session_state.processed_df["Created By"].isin(st.session_state.authorized_users)]
                    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, unusual_user_entries])
                    st.session_state.flagged_entries_by_category["Unauthorized Users"] = unusual_user_entries
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
                    st.session_state.flagged_entries_by_category["Post-Closing Entries"] = post_closing_entries
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
            st.session_state.flagged_entries_by_category["Below Authorization Threshold"] = below_threshold_entries

        # Check for 99999 pattern
        if st.session_state.nine_pattern_var:
            nine_pattern_entries = st.session_state.processed_df[
                st.session_state.processed_df["Debit Amount (Dr)"].apply(is_99999) |
                st.session_state.processed_df["Credit Amount (Cr)"].apply(is_99999)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, nine_pattern_entries])
            st.session_state.flagged_entries_by_category["99999 Pattern"] = nine_pattern_entries

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
                    st.session_state.flagged_entries_by_category["Suspicious Keywords"] = keyword_entries
            else:
                st.error("Column 'Entry Description' not found in the data.")
                return

        # Check for seldomly used accounts
        if st.session_state.seldomly_used_accounts_var:
            if st.session_state.processed_df is not None:
                # Count the frequency of each account number
                account_frequency = st.session_state.processed_df["Account Number"].value_counts().reset_index()
                account_frequency.columns = ["Account Number", "Transaction Count"]

                # Define seldomly used accounts as those with fewer than the specified threshold
                seldomly_used_accounts = account_frequency[account_frequency["Transaction Count"] < st.session_state.seldomly_used_accounts_threshold]

                # Flag entries for seldomly used accounts
                seldomly_used_entries = st.session_state.processed_df[
                    st.session_state.processed_df["Account Number"].isin(seldomly_used_accounts["Account Number"])
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
        if username == "m.elansary@maham.com" and password == "74107410":
            st.session_state.logged_in = True
            st.session_state.logged_in_user = username  # Store logged-in user
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
    uploaded_file = st.file_uploader("Import GL Dump CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.success("GL Dump CSV file imported successfully!")
        except Exception as e:
            st.error(f"Failed to import file: {e}")
            logging.error(f"Failed to import file: {e}")

    # Import Trial Balance
    st.subheader("Import Trial Balance")
    tb_uploaded_file = st.file_uploader("Import Trial Balance CSV", type=["csv"])
    if tb_uploaded_file is not None:
        try:
            st.session_state.trial_balance = pd.read_csv(tb_uploaded_file)
            st.success("Trial Balance CSV file imported successfully!")
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

    # Monthly Trial Balance
    st.header("4. Monthly Trial Balance")
    if st.button("Create Monthly Trial Balance"):
        create_monthly_trial_balance()

    # High-Risk Criteria & Testing
    st.header("5. High-Risk Criteria & Testing")
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

    # Export Reports
    st.header("6. Export Reports")
    if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
        # Export PDF Report
        if st.button("Export PDF Report"):
            pdf_output = export_pdf_report()
            st.download_button(
                label="Download PDF Report",
                data=pdf_output,
                file_name="audit_report.pdf",
                mime="application/pdf",
            )

        # Export Excel Report
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
