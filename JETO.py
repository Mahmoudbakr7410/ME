# Check for large transactions
if st.session_state.large_transactions_var:
    if "Debit Amount (Dr)" in st.session_state.processed_df.columns and "Credit Amount (Cr)" in st.session_state.processed_df.columns:
        large_entries = st.session_state.processed_df[
            (st.session_state.processed_df["Debit Amount (Dr)"] > st.session_state.large_threshold) |
            (st.session_state.processed_df["Credit Amount (Cr)"] > st.session_state.large_threshold)
        ]
        st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, large_entries])

# Check for manual journal entries
if st.session_state.manual_entries_var:
    if "Manual Entry Flag" in st.session_state.processed_df.columns:
        manual_entries = st.session_state.processed_df[st.session_state.processed_df["Manual Entry Flag"] == 1]
        st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, manual_entries])

# Check for suspense account transactions
if st.session_state.suspense_accounts_var:
    if "Suspense Account Flag" in st.session_state.processed_df.columns:
        suspense_entries = st.session_state.processed_df[st.session_state.processed_df["Suspense Account Flag"] == 1]
        st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, suspense_entries])

# Check for weekend transactions
if st.session_state.weekend_entries_var:
    if "Date" in st.session_state.processed_df.columns:
        weekend_entries = st.session_state.processed_df[st.session_state.processed_df["Date"].dt.weekday >= 5]  # Saturday (5) or Sunday (6)
        st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, weekend_entries])

# Check for offsetting transactions within same user & period
if st.session_state.offsetting_entries_var:
    if {"Created By", "Debit Amount (Dr)", "Credit Amount (Cr)", "Period/Month"}.issubset(st.session_state.processed_df.columns):
        offsetting_entries = st.session_state.processed_df.groupby(["Created By", "Period/Month"]).filter(
            lambda x: (x["Debit Amount (Dr)"].sum() - x["Credit Amount (Cr)"].sum()).abs() < 1e-6
        )
        st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, offsetting_entries])

# Check for duplicate transactions
if st.session_state.duplicate_entries_var:
    duplicate_entries = st.session_state.processed_df[st.session_state.processed_df.duplicated(
        subset=["Date", "Debit Amount (Dr)", "Credit Amount (Cr)", "Account ID"], keep=False
    )]
    st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, duplicate_entries])

# Check for transactions with no description
if st.session_state.no_description_var:
    if "Entry Description" in st.session_state.processed_df.columns:
        no_description_entries = st.session_state.processed_df[st.session_state.processed_df["Entry Description"].isna()]
        st.session_state.high_risk_entries = pd.concat([st.session_state.high_risk_entries, no_description_entries])
