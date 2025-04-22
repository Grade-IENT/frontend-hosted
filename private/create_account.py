import streamlit as st
import psycopg2
import bcrypt

def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        port=st.secrets["db_port"],
        dbname=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

# Hide the sidebar on this page
st.set_page_config(page_title="Create Account", layout="centered", initial_sidebar_state="collapsed")

st.title("Create Your Account")

email = st.text_input("Email")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Create Account"):
    if not email or not username or not password:
        st.error("Please fill in all fields.")
    else:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO UserAccount (username, userPassword, email) VALUES (%s, %s, %s)",
                            (username, hashed_pw, email))
                conn.commit()
                st.success("✅ Account created! Go back to login.")
        except psycopg2.errors.UniqueViolation:
            st.error("Username or email already exists.")
