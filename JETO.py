import streamlit as st
import pandas as pd
import pyodbc  # For connecting to Azure SQL Database

# Set up logging (optional, for debugging)
import logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started")

# Initialize session state variables
if 'df' not in st.session_state:
    st.session_state.df = None

# Function to connect to Azure SQL Database
def connect_to_azure_sql():
    server = "mahx.database.windows.net"
    database = "MAHx"
    username = "mahmoudbakr7410@gmail.com@mahx"
    password = "7oda@ELBASHA"
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(connection_string)
    return conn

# Function to retrieve data from Azure SQL Database
def retrieve_data_from_db():
    conn = connect_to_azure_sql()
    query = "SELECT * FROM dbo.Data"  # Retrieve all columns from the table
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Streamlit UI
def main_app():
    st.title("MAHAM DATA DEEP ANALYZER DEMO")

    # Data Retrieval
    st.header("1. Retrieve Data from Database")
    if st.button("Retrieve Data"):
        try:
            st.session_state.df = retrieve_data_from_db()
            st.success("Data retrieved successfully!")
        except Exception as e:
            st.error(f"Failed to retrieve data: {e}")
            logging.error(f"Failed to retrieve data: {e}")

    # Display Data
    if st.session_state.df is not None:
        st.header("2. Preview Data")
        st.write("Here is the data retrieved from the database:")
        st.dataframe(st.session_state.df)  # Display the data in a table

# Check if user is logged in (optional, for future use)
if not st.session_state.get("logged_in", False):
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
        # For now, allow any username/password to log in
        st.session_state.logged_in = True
        st.session_state.logged_in_user = username
        st.success("Logged in successfully!")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='footer'>Developed by Innovation and Transformation Team: Mahmoud Elansary and Sabeeh Uddin</div>", unsafe_allow_html=True)
else:
    main_app()
