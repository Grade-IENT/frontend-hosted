import streamlit as st
import pandas as pd
import psycopg2
import base64
from streamlit_searchbox import st_searchbox
from fuzzywuzzy import process

st.set_page_config(page_title= "Gradient - Professors", page_icon=":tada:", layout ="wide", initial_sidebar_state="expanded")

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

st.markdown(
    f'<div class="center-logo"></div>',
    unsafe_allow_html=True
)

def local_css(file_name):
    with open(file_name) as f :
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style/style.css")


# with st.container():
#      st.write("Go to :")
#      left, middle, right = st.columns(3)
#      with middle:          
#         if st.button("Four Year Plan", use_container_width= True):
#             st.switch_page("pages/four_year.py")
    
#      with left:

#         if st.button("Profile", use_container_width= True):
#             st.switch_page("pages/profile.py")

#      with right:
#         if st.button("Scheduling", use_container_width=True):
#             st.switch_page("pages/schedule.py")

#      st.write("---")

def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        port=st.secrets["db_port"],
        dbname=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

def get_letter_grade(sqi):
    if sqi == -1:
        return '', 'black'
    if sqi < 60:
        return 'F', 'red'
    if sqi < 63:
        return 'D-', 'orange'
    if sqi < 67:
        return 'D', 'orange'
    if sqi < 70:
        return 'D+', 'orange'
    if sqi < 73:
        return 'C-', '#FFD700' # darker yellow for visibility
    if sqi < 77:
        return 'C', '#FFA600'
    if sqi < 80:
        return 'C+', '#FFA600'
    if sqi < 83:
        return 'B-', 'yellowgreen'
    if sqi < 87:
        return 'B', 'yellowgreen'
    if sqi < 90:
        return 'B+', 'yellowgreen'
    if sqi < 93:
        return 'A-', 'limegreen'
    if sqi < 97:
        return 'A', 'limegreen'
    if sqi <= 100:
        return 'A+', 'limegreen'

def approx_score(x):
    """
    Cubic on [0,5] → [0,100], strictly increasing,
    with f(0)=0, f(5)=100, fitted to your sample points.
    """
    a, b, c = -1.26900567,  8.69005666, 8.27485836
    return a*x**3 + b*x**2 + c*x

def render_prof_card(row):
    name = row["Professor Name"]
    chk_key = f"pinchk_{name}"

    # 1) Seed the checkbox’s initial state once
    if chk_key not in st.session_state:
        st.session_state[chk_key] = name in st.session_state.pinned_profs

    # 2) Define a callback that runs *before* rerun
    def _toggle_pin():
        if st.session_state[chk_key]:
            # user just checked it
            if name not in st.session_state.pinned_profs:
                st.session_state.pinned_profs.append(name)
        else:
            # user just unchecked it
            if name in st.session_state.pinned_profs:
                st.session_state.pinned_profs.remove(name)

    # 3) Render the checkbox with that callback
    chk = st.checkbox(
        "📌 Pin to top",
        key=chk_key,
        on_change=_toggle_pin
    )

    # 4) Then your existing card markup
    sqi = round(approx_score(row["SQI"]) if pd.notnull(row["SQI"]) else -1, 2)
    letter, color = get_letter_grade(sqi)
    st.markdown(f"""
    <div style="background:#f5f5f5;padding:15px;border-radius:10px;margin-bottom:10px">
      <h5>{name}</h5>
      <strong>SQI:</strong>
      <span style="color:{color}">{letter} ({sqi if sqi != -1 else 'N/A'})</span>
      <div style="margin-top:15px;padding:15px;
                  background:#f9f9f9;border-left:4px solid #bbb;
                  border-radius:8px">
        <p style="margin:0 0 5px;"><strong>Summary:</strong></p>
        <p style="margin:0;color:#333">{row['Summary']}</p>
      </div>
      <div style="font-size: 0.85em; color: #666; background-color: #f0f0f0; padding: 8px; border-radius: 6px; margin-top: 10px;">
        <em>Summaries are AI compilations of real RMP reviews and may not be 100% accurate. </em>
      </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=600)  # cache for 10 minutes
def load_professors():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT prof_name, SQI, summary
    FROM professor
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return pd.DataFrame(rows, columns=["Professor Name", "SQI", "Summary"])

with st.container():
    if "pinned_profs" not in st.session_state:
        st.session_state.pinned_profs = []
    st.title("Professor Lookup",anchor=False)
    
    df = load_professors()
    prof_names = df["Professor Name"].tolist()

    def search_professors(search_term: str):
        if not search_term:
            return []
        return [name for name, _ in process.extract(search_term, prof_names, limit=5)]
    
    if len(df.index) != 0:
        with st.container(border=True):
            st.text("Search up your professors and find their ratings!")
            # selected_prof = st_searchbox(
            #     search_professors,
            #     debounce=0,
            #     key="prof_search",
            #     rerun_on_update=False,
            #     placeholder="Search for a professor by name...")
            selected_prof = st.selectbox(
                label="Search up your professors and find their ratings!",
                label_visibility="collapsed",
                options=prof_names,
                index=None, # initially empty 
                placeholder="Search for a professor by name...")

        # selected_prof = st_searchbox(search_professors, placeholder="Search for a Professor...")

        # 1) Always show pinned first
        if st.session_state.pinned_profs: 
            st.subheader("📌 Pinned Professors",anchor=None)
            for prof_name in st.session_state.pinned_profs.copy():
                row = df[df["Professor Name"] == prof_name]
                if not row.empty:
                    render_prof_card(row.iloc[0])

        # 2) Then show the current search hit (if any), but only if it’s not already pinned
        if selected_prof and selected_prof not in st.session_state.pinned_profs:
            row = df[df["Professor Name"] == selected_prof]
            if not row.empty:
                st.subheader("Search Result")
                render_prof_card(row.iloc[0])
