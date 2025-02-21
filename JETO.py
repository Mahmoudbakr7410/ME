import streamlit as st
import pandas as pd
import numpy as np
import logging
import math
from io import StringIO
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta

# Enhanced Logging with Timestamps and File Handling
log_file = "maHx_jet_app.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
logger = logging.getLogger(__name__)  # More specific logger

# Initialize Session State with More Structure
if 'data' not in st.session_state:
    st.session_state.data = {
        'df': None,
        'processed_df': None,
        'high_risk_entries': None,
        'column_mapping': {},
        'authorized_users': [],
        'closing_date': None,
        'public_holidays': [],
        'rounded_threshold': 100.0,
        'test_criteria': {  # Group test criteria
            'public_holidays': False,
            'rounded_numbers': False,
            'unusual_users': False,
            'post_closing': False,
        }
    }

# Constants and Field Definitions (More Organized)
REQUIRED_FIELDS = ["Transaction ID", "Date", "Debit Amount (Dr)", "Credit Amount (Cr)"]
OPTIONAL_FIELDS = [
    "Journal Entry ID", "Posting Date", "Entry Description", "Document Number",
    "Period/Month", "Year", "Entry Type", "Reversal Indicator", "Account ID", "Account Name",
    "Account Type", "Cost Center", "Subledger Type", "Subledger ID", "Currency", "Local Currency Amount",
    "Exchange Rate", "Net Amount", "Created By", "Approved By", "Posting User", "Approval Date",
    "Journal Source", "Manual Entry Flag", "High-Risk Account Flag", "Suspense Account Flag",
    "Offsetting Entry Indicator", "Period-End Flag", "Weekend/Holiday Flag", "Round Number Flag"
]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

# Data Type Conversion with Enhanced Handling
def convert_data_types(df):
    numeric_fields = ["Debit Amount (Dr)", "Credit Amount (Cr)", "Local Currency Amount", "Net Amount", "Exchange Rate"] # Expand numeric fields
    date_fields = ["Date", "Posting Date", "Approval Date"] # Expand date fields

    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0)  # Fill NaN with 0 after numeric conversion

    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors="coerce")

    return df

# High-Risk Testing Logic (Improved and More Modular)
def is_rounded(value, threshold):
    try:
        value = float(value)
        return (value % threshold == 0) or math.isclose(value % threshold, threshold, rel_tol=1e-9) # Increased tolerance
    except (ValueError, TypeError):
        return False

def check_public_holidays(df, holidays):
    return df[df["Date"].isin(holidays)] if "Date" in df.columns else pd.DataFrame()

def check_rounded_numbers(df, threshold):
    return df[df["Debit Amount (Dr)"].apply(lambda x: is_rounded(x, threshold)) | df["Credit Amount (Cr)"].apply(lambda x: is_rounded(x, threshold))]

def check_unusual_users(df, authorized_users):
    return df[~df["Created By"].isin(authorized_users)] if "Created By" in df.columns and authorized_users else pd.DataFrame()

def check_post_closing(df, closing_date):
    return df[df["Date"] > closing_date] if "Date" in df.columns and closing_date else pd.DataFrame()


def perform_high_risk_test():
    df = st.session_state.data['processed_df']
    if df is None or df.empty:
        st.warning("No data to test. Please import and process a CSV file first.")
        return

    st.session_state.data['high_risk_entries'] = pd.DataFrame()  # Initialize

    if st.session_state.data['test_criteria']['public_holidays']:
        st.session_state.data['high_risk_entries'] = pd.concat([st.session_state.data['high_risk_entries'], check_public_holidays(df, st.session_state.data['public_holidays'])])
    if st.session_state.data['test_criteria']['rounded_numbers']:
        st.session_state.data['high_risk_entries'] = pd.concat([st.session_state.data['high_risk_entries'], check_rounded_numbers(df, st.session_state.data['rounded_threshold'])])
    if st.session_state.data['test_criteria']['unusual_users']:
        st.session_state.data['high_risk_entries'] = pd.concat([st.session_state.data['high_risk_entries'], check_unusual_users(df, st.session_state.data['authorized_users'])])
    if st.session_state.data['test_criteria']['post_closing']:
        st.session_state.data['high_risk_entries'] = pd.concat([st.session_state.data['high_risk_entries'], check_post_closing(df, st.session_state.data['closing_date'])])

    if not st.session_state.data['high_risk_entries'].empty:
        st.success(f"Found {len(st.session_state.data['high_risk_entries'])} high-risk entries.")
    else:
        st.success("No high-risk entries found.")

# Streamlit UI (Improved Layout and User Experience)

st.title("MAHx-JET - Maham for Professional Services")

# Data Import & Processing (Clearer Sections)
st.header("1. Data Import")
uploaded_file = st.file_uploader("Import CSV", type=["csv"])

if uploaded_file:
    try:
        st.session_state.data['df'] = pd.read_csv(uploaded_file)
        st.success("CSV file imported successfully!")

        st.subheader("2. Column Mapping")
        for field in ALL_FIELDS:
            st.session_state.data['column_mapping'][field] = st.selectbox(f"Map '{field}' to:", [""] + list(st.session_state.data['df'].columns))

        if st.button("Confirm Mapping"):
            missing_fields = [field for field in REQUIRED_FIELDS if st.session_state.data['column_mapping'][field] == ""]
            if missing_fields:
                st.error(f"Missing required fields: {missing_fields}")
            else:
                st.session_state.data['processed_df'] = st.session_state.data['df'].rename(columns={v: k for k, v in st.session_state.data['column_mapping'].items() if v != ""})
                st.session_state.data['processed_df'] = convert_data_types(st.session_state.data['processed_df'])
                st.success("Columns mapped and data processed successfully!")
                st.dataframe(st.session_state.data['processed_df'].head()) # Display a preview

    except Exception as e:
        st.error(f"Error during import/processing: {e}")
        logger.error(f"Import/Processing Error: {e}")

# High-Risk Criteria & Testing (Organized Checkboxes)
st.header("3. High-Risk Criteria")
col1, col2 = st.columns(2)  # Use columns for better layout

with col1:
    st.session_state.data['test_criteria']['public_holidays'] = st.checkbox("Public Holidays")
    if st.session_state.data['test_criteria']['public_holidays']:
        holidays_str = st.text_area("Enter Public Holidays (YYYY-MM-DD, comma-separated):")
        try:  # Handle potential date parsing errors
            st.session_state.data['public_holidays'] = [pd.to_datetime(d.strip()) for d in holidays_str.split(',') if d.strip()]
        except ValueError:
            st.error("Invalid date format. Please use YYYY-MM-DD, separated by commas.")

    st.session_state.data['test_criteria']['rounded_numbers'] =
