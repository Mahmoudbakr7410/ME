import streamlit as st
import pandas as pd
import logging
import math
from io import StringIO
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas

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

# Export to PDF
def export_to_pdf(df):
    if df is not None and not df.empty:
        # Create a PDF file in a BytesIO buffer
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, height - 30, "High-Risk Journal Entries Report")
        c.setFont("Helvetica", 10)
        c.drawString(30, height - 50, f"Total High-Risk Entries: {len(df)}")

        # Table Headers
        headers = df.columns.tolist()
        x_start = 30
        y_start = height - 80
        row_height = 20

        # Draw table headers
        for i, header in enumerate(headers):
            c.setFillColor(colors.black)
            c.drawString(x_start + i * 100, y_start, header)

        # Draw table data
        y_pos = y_start - row_height
        for index, row in df.iterrows():
            for i, value in enumerate(row):
                c.drawString(x_start + i * 100, y_pos, str(value))
            y_pos -= row_height

        c.save()
        output.seek(0)
        return output
    return None

# Streamlit UI
st.title("MAHx-JET - Maham for Professional Services")

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
