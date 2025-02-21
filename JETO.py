import streamlit as st
import pandas as pd
import logging
import math
from io import StringIO

# Set up logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started")

# Initialize session state variables
if 'df' not in st.session_state:
    st.session_state.df = None
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'high_risk_entries' not in st.session_state:
    st.session_state.high_risk_entries = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}
if 'closing_date' not in st.session_state:
    st.session_state.closing_date = None

# Function to check for rounded numbers
def is_rounded(value, threshold):
    try:
        value = float(value)
        return (value % threshold == 0) or (math.isclose(value % threshold, threshold, rel_tol=1e-6))
    except (ValueError, TypeError):
        return False

# Function to check Benford's Law anomalies
def benfords_law_check(series):
    expected_freq = [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6]  # Benford's expected % for 1-9
    actual_freq = [0] * 9

    series = series.dropna().astype(str)
    for value in series:
        first_digit = int(str(abs(float(value)))[0]) if value[0].isdigit() else None
        if first_digit and 1 <= first_digit <= 9:
            actual_freq[first_digit - 1] += 1

    total = sum(actual_freq)
    if total == 0:
        return None  # No data

    actual_percent = [(x / total) * 100 for x in actual_freq]
    deviations = [abs(actual_percent[i] - expected_freq[i]) for i in range(9)]
    
    return sum(deviations) > 15  # Flag if deviation exceeds 15%

# Function to detect fraud risk transactions
def perform_high_risk_test():
    if st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("No data to test. Please import a CSV file first.")
        return

    try:
        st.session_state.high_risk_entries = pd.DataFrame()
        df = st.session_state.processed_df

        # Rounded numbers
        if st.session_state.rounded_var:
            rounded_entries = df[
                df["Debit Amount (Dr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold)) |
                df["Credit Amount (Cr)"].apply(lambda x: is_rounded(x, st.session_state.rounded_threshold))
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, rounded_entries])

        # Benford’s Law anomalies
        if st.session_state.benford_var and "Debit Amount (Dr)" in df.columns:
            if benfords_law_check(df["Debit Amount (Dr)"]) or benfords_law_check(df["Credit Amount (Cr)"]):
                st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, df])

        # Same user creates & approves
        if st.session_state.same_user_var and "Created By" in df.columns and "Approved By" in df.columns:
            same_user_entries = df[df["Created By"] == df["Approved By"]]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, same_user_entries])

        # Backdated Transactions
        if st.session_state.backdated_var and "Posting Date" in df.columns and st.session_state.closing_date:
            backdated_entries = df[df["Posting Date"] < st.session_state.closing_date]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, backdated_entries])

        # Entries Just Below Approval Threshold
        if st.session_state.approval_threshold_var and "Debit Amount (Dr)" in df.columns:
            threshold = st.session_state.approval_threshold
            suspicious_entries = df[
                ((df["Debit Amount (Dr)"] >= threshold * 0.95) & (df["Debit Amount (Dr)"] <= threshold)) |
                ((df["Credit Amount (Cr)"] >= threshold * 0.95) & (df["Credit Amount (Cr)"] <= threshold))
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, suspicious_entries])

        # Duplicate Transactions
        if st.session_state.duplicate_var and "Transaction ID" in df.columns:
            duplicate_entries = df[df.duplicated(subset=["Transaction ID"], keep=False)]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, duplicate_entries])

        # Unusual Vendor Payments
        if st.session_state.unusual_vendor_var and "Vendor" in df.columns:
            unusual_vendor_entries = df[df["Vendor"].str.contains("cash|unknown|suspense", case=False, na=False)]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, unusual_vendor_entries])

        # Large Round Transactions at Odd Hours
        if st.session_state.odd_hour_var and "Time" in df.columns:
            odd_hour_entries = df[
                (df["Time"].str.contains("00:|01:|02:|03:", na=False)) & 
                (df["Debit Amount (Dr)"] > st.session_state.rounded_threshold) |
                (df["Credit Amount (Cr)"] > st.session_state.rounded_threshold)
            ]
            st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, odd_hour_entries])

        if not st.session_state.high_risk_entries.empty:
            st.success(f"Found {len(st.session_state.high_risk_entries)} high-risk entries.")
        else:
            st.success("No high-risk entries found.")

    except Exception as e:
        st.error(f"Error during testing: {e}")
        logging.error(f"Error during high-risk testing: {e}")

# Streamlit UI
st.title("MAHx-JET - Maham for Professional Services")

st.header("1. High-Risk Fraud Detection")

st.session_state.rounded_var = st.checkbox("Rounded Numbers")
st.session_state.benford_var = st.checkbox("Benford’s Law Anomalies")
st.session_state.same_user_var = st.checkbox("Same User Creates & Approves")
st.session_state.backdated_var = st.checkbox("Backdated Transactions")
st.session_state.approval_threshold_var = st.checkbox("Entries Below Approval Threshold")
st.session_state.duplicate_var = st.checkbox("Duplicate Transactions")
st.session_state.unusual_vendor_var = st.checkbox("Unusual Vendor Payments")
st.session_state.odd_hour_var = st.checkbox("Large Round Numbers at Odd Hours")

if st.session_state.approval_threshold_var:
    st.session_state.approval_threshold = st.number_input("Approval Threshold:", value=50000.0)

if st.button("Run Fraud Tests"):
    perform_high_risk_test()

# Export Reports
if st.session_state.high_risk_entries is not None and not st.session_state.high_risk_entries.empty:
    csv = st.session_state.high_risk_entries.to_csv(index=False)
    st.download_button("Download Fraud Report CSV", csv, "high_risk_fraud.csv", "text/csv")

