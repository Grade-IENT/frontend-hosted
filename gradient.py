import streamlit as st
import psycopg2
import bcrypt
import base64

st.set_page_config(page_title="Gradient - Login", layout="wide", initial_sidebar_state="collapsed")

def load_css():
   with open("./style/style.css") as f:  # Make sure the path to your CSS is correct
       st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# hides the white space at the top (header)
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
</style>
""",unsafe_allow_html=True)

# Inject CSS for as full‐page animated gradient
st.markdown(
    """
    <style>
    /* Static left‑half gradient, right half white */
    html, body, .stApp {
        margin: 0; 
        padding: 0; 
        height: 100%;
        background:
            linear-gradient(
                to right,
                #4c69f3,
                #8c4bbf,
                #f51b86,
                #ff375f
            ) 0% 0% / 100% 100% no-repeat,
            /* white for the rest */
            white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Now you can build the rest of your UI on top of that animated background

# DB connection (No changes here)
def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        port=st.secrets["db_port"],
        dbname=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

@st.dialog(" ", width="large")
def show_create_account_form():
    st.markdown(
    """
    <h2 style="
      text-align: center;
      color: #8c4bbf;
      white-space: nowrap;
      font-size: 2.5rem;
      margin-bottom: 1.5rem;
    ">
      Create Your Account
    </h2>
    """,
    unsafe_allow_html=True
)
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    create_account = st.button("Create Account")

    

    
    if email and username and password:
        if create_account:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            try:
                with get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO UserAccount (username, userPassword, email) VALUES (%s, %s, %s)",
                                (username, hashed_pw, email))
                    conn.commit()
                    st.success("Account created! Go back to login.")
                    st.session_state["create_account"] = False
                    st.rerun()
            except psycopg2.errors.UniqueViolation:
                st.error("Username or email already exists.")
    else:
        st.error("Please fill in all fields.")
 



# Create three equal columns
col1, col2, col3 = st.columns(3)

# Leave the first and third empty, render your card in the second
with col2:
    # Start a white‑background “card”
    
    st.markdown(
        """
        <style>
        /* Select the middle column in every horizontal block */
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
            background-color: white !important;
            padding: 1rem !important;           /* optional: inner padding */
            border-radius: 8px !important;      /* optional: rounded corners */
            box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important; /* optional: shadow */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # Logo
    with open("logo.png", "rb") as logo_file:
        encoded_logo = base64.b64encode(logo_file.read()).decode()
    st.markdown(
        f'<img src="data:image/png;base64,{encoded_logo}" '
        "style='display:block; margin:0 auto 0rem; height:120px;'>",
        unsafe_allow_html=True,
    )

  
    # Inputs
    username = st.text_input("Username or email:")
    password = st.text_input("Password:", type="password")
    remember_me = st.checkbox("Remember me")

    # Sign In button
    if st.button("Sign In"):
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, userPassword FROM UserAccount WHERE username = %s",
                (username,),
            )
            result = cur.fetchone()
        if result and bcrypt.checkpw(password.encode(), result[1].encode()):
            st.session_state["user_id"] = result[0]
            st.success("✅ Logged in successfully!")
            st.switch_page("pages/profile.py")
        else:
            st.error("Invalid username or password.")

    # “Create Account” toggle
    if "create_account" not in st.session_state:
        st.session_state["create_account"] = False
    if st.button("New here? Create an Account"):
        st.session_state["create_account"] = True
    if st.session_state["create_account"]:
        show_create_account_form()

    # Close the card div
    st.markdown("</div>", unsafe_allow_html=True)
