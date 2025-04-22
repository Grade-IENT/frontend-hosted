import streamlit as st
import psycopg2
import pandas as pd
import base64



# --- DB Connection ---
def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        port=st.secrets["db_port"],
        dbname=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

# --- Login Check ---
if "user_id" not in st.session_state:
    st.error("🚫 You must be logged in to view this page.")
    st.stop()

# --- Get Username ---
with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT username FROM UserAccount WHERE id = %s", (st.session_state["user_id"],))
    result = cur.fetchone()
    username = result[0] if result else "Unknown User"

# --- Page Config & CSS ---
st.set_page_config(page_title=f"Gradient - {username}'s Profile", page_icon=":tada:", layout="wide", initial_sidebar_state="expanded")
def load_logo_as_base64(logo_path):
    with open(logo_path, "rb") as logo_file:
        encoded_logo = base64.b64encode(logo_file.read()).decode()
    return encoded_logo

logo_base64 = load_logo_as_base64("logo.png")

st.markdown(
    f"""
    <style>
        .center-logo {{
            display: flex;
            justify-content: center;  /* Center horizontally */
            align-items: center;      /* Center vertically */
            height: 150px;            /* Full viewport height */
            background: url('data:image/png;base64,{logo_base64}') no-repeat center center; /* Set the image as background */
            background-size: contain; /* Ensure the logo scales nicely */
            width: 100%;              /* Full width of the container */
           padding: 0;               /* Remove extra padding */
        }}
        .stApp {{
            background: white !important; /* Apply white background */
        }}
    </style>
    """, unsafe_allow_html=True
)

# Display the div with centered background logo
st.markdown(
    f'<div class="center-logo"></div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        #logout-menu {
            position: fixed;
            top: 1.2rem;
            right: 2rem;
            background-color: #f8f9fa;
            padding: 0.5rem 1rem;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            z-index: 9999;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Load external style ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

# --- Top-right Logout Dropdown ---
# ⬅️ Style and HTML for dropdown
# ⬅️ Style for top-right dropdown
st.markdown("""
<style>
#logout-menu {
    position: fixed;
    top: 1.2rem;
    right: 2rem;
    background-color: white;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    z-index: 9999;
    width: auto;
}
#logout-menu details {
    cursor: pointer;
}
#logout-menu summary {
    list-style: none;
    font-weight: 600;
}
/* Style for the logout button to make it text-like */
#logout-button {
    background: none;
    border: none;
    color: #ff0000; /* Red text */
    cursor: pointer;
    padding: 5px 0;
    margin-top: 5px;
    text-align: left;
    font-size: 14px;
}
#logout-button:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

# ⬅️ Dropdown HTML for logout
st.markdown(f"""
<div id="logout-menu">
  <details>
    <summary>{username} ⏷</summary>
    <form method='post'>
        <button id="logout-button" type="submit" name="logout">Log Out</button>
    </form>
  </details>
</div>
""", unsafe_allow_html=True)

# ⬅️ Handle logout event
if st.session_state.get("logout"):
    st.session_state.clear()
    st.switch_page("gradient.py")
# --- Header Section ---
with st.container():
    st.title(f"{username}'s Profile")

    # info, picture = st.columns((5, 2))
    # with info:
    st.write("---")
    st.write("Intended Major: N/A")
    st.write("Completed Credits: N/A")
    st.write("GPA: N/A")

    # with picture:
        # st.image("blankprofilepic.jpg", caption="Profile Picture", width=200)

    st.write("---")

with st.expander("Four Year Plan"):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT year, semester, course_display
            FROM PlanCourse
            WHERE user_id = %s
            ORDER BY year, semester, id
        """, (st.session_state["user_id"],))
        rows = cur.fetchall()

    if not rows:
        st.info("No saved plan found. Go to the Four Year Plan tab to generate one.")
    else:
        # Organize by year and semester
        plan = { (year, semester): [] for year in range(1, 5) for semester in ("Fall", "Spring") }
        for year, semester, display in rows:
            plan[(year, semester)].append(display)

        for year in range(1, 5):
            st.subheader(f"Year {year}")
            col_fall, col_spring = st.columns(2)
            for semester, col in zip(("Fall", "Spring"), (col_fall, col_spring)):
                with col:
                    sem_courses = plan[(year, semester)]
                    st.markdown(f"**{semester}**")

                    if not sem_courses:
                        st.write("_No courses scheduled._")
                    else:
                        parsed = []
                        for entry in sem_courses:
                            try:
                                code, rest = entry.split(' ', 1)
                                name, rest = rest.rsplit('(', 1)
                                credits_part, sqi_part = rest.rstrip(')').split(', SQI ')
                                credits = credits_part.strip().replace('cr', '').strip()
                                sqi = float(sqi_part.strip())
                                parsed.append({
                                    "Course Code": code.strip(),
                                    "Course Name": name.strip(),
                                    "Credits": int(credits),
                                    "SQI": sqi
                                })
                            except Exception:
                                parsed.append({
                                    "Course Code": "",
                                    "Course Name": entry.strip(),
                                    "Credits": "",
                                    "SQI": ""
                                })

                        df = pd.DataFrame(parsed)
                        df = df[["Course Code", "Course Name", "Credits", "SQI"]]
                        st.dataframe(df.style.hide(axis="index"), hide_index=True, use_container_width=True)

                        valid_sqis = [row["SQI"] for row in parsed if isinstance(row["SQI"], float)]
                        if valid_sqis:
                            avg_sqi = sum(valid_sqis) / len(valid_sqis)
                            st.markdown(f"Average SQI: **{avg_sqi:.2f}**")
                        else:
                            st.markdown("Average SQI: **N/A**")