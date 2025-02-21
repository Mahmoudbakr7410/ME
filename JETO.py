import streamlit as st
import pandas as pd
import logging
import math
from io import StringIO
from io import BytesIO
from fpdf import FPDF

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

# Export to Excel
def export_to_excel(df):
    if df is not None and not df.empty:
        # Save the dataframe to Excel in a BytesIO buffer
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return output
    return None

# Export to PDF using fpdf
def export_to_pdf(df):
    if df is not None and not df.empty:
        # Create a PDF file
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="High-Risk Journal Entries Report", ln=True, align="C")

        # Table headers
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 10)
        headers = df.columns.tolist()
        for header in headers:
            pdf.cell(30, 10, header, border=1)
        pdf.ln()

        # Table rows
        pdf.set_font("Arial", '', 10)
        for _, row in df.iterrows():
            for value in row:
                pdf.cell(30, 10, str(value), border=1)
            pdf.ln()

        # Save to buffer
        output = BytesIO()
        pdf.output(output)
        output.seek(0)
        return output
    return None

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
    all_fields = [
        "Transaction ID", "Date", "Debit Amount (Dr)", "Credit Amount (Cr)", 
        "Journal Entry ID", "Posting Date", "Entry Description", "Document Number",
        "Period/Month", "Year", "Entry Type", "Reversal Indicator", "Account ID", "Account Name",
        "Account Type", "Cost Center", "Subledger Type", "Subledger ID", "Currency", "Local Currency Amount",
        "Exchange Rate", "Net Amount", "Created By", "Approved By", "Posting User", "Approval Date",
        "Journal Source", "Manual Entry Flag", "High-Risk Account Flag", "Suspense Account Flag",
        "Offsetting Entry Indicator", "Period-End Flag", "Weekend/Holiday Flag", "Round Number Flag"
    ]
    for field in all_fields:
        st.session_state.column_mapping[field] = st.selectbox(f"Map '{field}' to:", [""] + st.session_state.df.columns.tolist())
    
    if st.button("Confirm Mapping"):
        missing_fields = [field for field in ["Transaction ID", "Date", "Debit Amount (Dr)", "Credit Amount (Cr)"] if st.session_state.column_mapping[field] == ""]
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

# Export Reports
st.header("3. Export Reports")
if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
    if st.button("Export High-Risk Entries"):
        # Export to CSV
        csv = st.session_state.high_risk_entries.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="high_risk_entries.csv",
            mime="text/csv",
        )

        # Export to Excel
        excel_file = export_to_excel(st.session_state.high_risk_entries)
        if excel_file:
            st.download_button(
                label="Download Excel",
                data=excel_file,
                file_name="high_risk_entries.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # Export to PDF
        pdf_file = export_to_pdf(st.session_state.high_risk_entries)
        if pdf_file:
            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name="high_risk_entries_report.pdf",
                mime="application/pdf",
            )
else:
    st.warning("No high-risk entries to export. Please run the test first.")
