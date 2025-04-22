import streamlit as st
import pandas as pd
import psycopg2
from pathlib import Path
import sys
import numpy as np
import base64


# ─────────────── Add repo root to path ───────────────
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ─────────────── Import scheduler ───────────────
from course_scheduler import build_plan, DEFAULT_MIN_CR, DEFAULT_MAX_CR

# ─────────────── Paths & Constants ───────────────
DATA_DIR = Path(__file__).resolve().parents[1] / "4_Year_input_Data"
AP_CREDIT_CSV = DATA_DIR / "rutgers_ap_credits.csv"

MAJOR_CSV = {
    "Aerospace Engineering":                 "aerospace_engineering_courses.csv",
    "Biomedical Engineering":                "biomedical_engineering_courses.csv",
    "Biochemical Engineering":               "biochemical_engineering_courses.csv",
    "Chemical Engineering":                  "chemical_engineering_courses.csv",
    "Civil Engineering":                     "civil_engineering_courses.csv",
    "Environmental Engineering":             "environmental_engineering_courses.csv",
    "Computer Engineering":                  "computer_engineering_courses.csv",
    "Electrical Engineering":                "electrical_engineering_courses.csv",
    "Industrial and Systems Engineering":    "industrial_systems_engineering_courses.csv",
    "Materials Science Engineering":         "materials_science_engineering_courses.csv",
    "Mechanical Engineering":                "mechanical_engineering_courses.csv",
    "Packaging Engineering":                 "packaging_engineering_courses.csv",
}

# ─────────────── Page setup ───────────────
st.set_page_config(page_title="Gradient – Four‑Year Plan", page_icon=":tada:", layout="wide", initial_sidebar_state="expanded")

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

# use CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

st.markdown("""
<style>
    div[data-testid="collapsedControl"] 
    div[data-baseweb="slider"] {
        background-color: white !important;
        padding: 10px;
        border-radius: 8px;
    }
    input[type="range"] { accent-color: black !important; }
    div[data-baseweb="slider"] span {
        color: black !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# with st.container():
#     st.write("Go to:")
#     left, middle, right = st.columns(3)
#     with left:
#         if st.button("Profile", use_container_width=True):
#             st.switch_page("pages/profile.py")
#     with middle:
#         if st.button("Professors", use_container_width=True):
#             st.switch_page("pages/professors.py")
#     with right:
#         if st.button("Scheduling", use_container_width=True):
#             st.switch_page("pages/schedule.py")
#     st.write("---")

# Inputs
st.title("Four Year Plan")

majors = list(MAJOR_CSV.keys())
col1, col2 = st.columns(2)
major = st.selectbox("Select Major", ["Select a major"] + majors)

cr_col1, cr_col2 = st.columns([1, 1])
with cr_col1:
    min_cr = st.number_input("Min Credits / Semester", value=DEFAULT_MIN_CR, min_value=6, max_value=18)
with cr_col2:
    max_cr = st.number_input("Max Credits / Semester", value=DEFAULT_MAX_CR, min_value=min_cr, max_value=21)

# ─────────────── AP Section ───────────────
ap_catalog = pd.read_csv(AP_CREDIT_CSV, dtype=str)
exams = sorted(ap_catalog["AP Exam"].unique())

st.markdown("### Optional: Add AP Credits")
chosen = st.multiselect("Select AP Exams", exams)
ap_scores = {exam: int(st.slider(f"{exam} score", 1, 5, 5, key=exam)) for exam in chosen}


# DB connection function
def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        port=st.secrets["db_port"],
        dbname=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

# Save to DB logic
if 'clicked' not in st.session_state:
    st.session_state.clicked = {1:False,2:False}

def clicked(button):
    st.session_state.clicked[button] = True

build_btn = st.button("Build Plan", use_container_width=True, on_click=clicked, args=[1])


def save_plan_to_db(df):
    if "user_id" not in st.session_state:
        st.error("You must be logged in to save your plan.")
        return

    try:
        with get_connection() as conn:
            cur = conn.cursor()

            # Clear previous saved plan
            cur.execute("DELETE FROM PlanCourse WHERE user_id = %s", (st.session_state["user_id"],))

            total_inserted = 0

            for sem_idx, column in enumerate(df.columns):
                year = (sem_idx // 2) + 1
                semester = "Fall" if sem_idx % 2 == 0 else "Spring"

                for entry in df[column].dropna():
                    display_str = entry.strip()
                    course_code = None
                    class_id = None

                    try:
                        # Try to get course_code like "332:231"
                        parts = entry.split()
                        if parts and ":" in parts[0]:
                            course_code = parts[0]
                            cur.execute("SELECT id FROM Class WHERE course_code = %s", (course_code,))
                            result = cur.fetchone()
                            if result:
                                class_id = result[0]

                        # Insert every instance — including duplicates
                        cur.execute(
                            """
                            INSERT INTO PlanCourse (user_id, class_id, year, semester, course_display)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (st.session_state["user_id"], class_id, year, semester, display_str)
                        )
                        total_inserted += 1

                    except Exception as e:
                        st.warning(f"⚠️ Could not save entry: {entry} — {e}")

            conn.commit()
            st.success(f"✅ Plan saved! {total_inserted} entries added.")

    except psycopg2.Error as e:
        st.error(f"❌ Database error: {e.pgerror}")

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
        return 'C-', '#FFA600' # darker yellow for visibility
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

# ─────────────── Generate Plan ───────────────

if st.session_state.clicked[1] and major in majors:
    st.session_state["build_btn"] = True
    csv_path = DATA_DIR / MAJOR_CSV[major]
    if not csv_path.exists():
        st.error(f"Catalog file not found: **{csv_path}**")
        st.stop()

    sched, sem_credits, df = build_plan(csv_path, ap_scores, min_cr=int(min_cr), max_cr=int(max_cr), mode="var")

    st.markdown(f"### Showing 4-Year Plan for **{major}**")

    for year in range(4):
        st.subheader(f"Year {year + 1}")
        col_fall, col_spring = st.columns(2)
        for sem_idx, col in zip((year * 2, year * 2 + 1), (col_fall, col_spring)):
            with col:
                sem_name = f"Semester {sem_idx + 1}"
                raw_rows = df[sem_name].replace("", pd.NA).dropna().tolist()

                parsed = []
                for entry in raw_rows:
                    try:
                        code, rest = entry.split(' ', 1)
                        name, rest = rest.rsplit('(', 1)
                        credits_part, sqi_part = rest.rstrip(')').split(', SQI ')
                        credits = credits_part.strip().replace('cr', '').strip()
                        sqi = float(sqi_part.strip())*10 + 50
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

                parsed_df = pd.DataFrame(parsed)
                parsed_df.columns = ["Course Code", "Course Name", "Credits", "SQI"]

                st.markdown(f"**{sem_name}** — Total Credits: **{sem_credits[sem_idx]}**")

                valid_sqis = [row["SQI"] for row in parsed if isinstance(row["SQI"], float)]
                if valid_sqis:
                    avg_sqi = sum(valid_sqis) / len(valid_sqis)
                    letter_grade, color = get_letter_grade(avg_sqi)
                    st.html(f"Average SQI: <strong style = \'color: {color}\'>{letter_grade} ({avg_sqi:.2f})</strong>")
                else:
                    st.markdown("Average SQI: **N/A**")

                st.dataframe(parsed_df.style.hide(axis="index").format({"SQI": "{:.2f}"}), hide_index=True, use_container_width=True)

    # Download and Save buttons
    col_dl, col_save = st.columns([2, 1])
    with col_dl:
        st.download_button("Download Plan as CSV",
                           data=df.to_csv(index=False).encode(),
                           file_name="four_year_plan.csv")
    with col_save:
        
        if st.session_state.get("build_btn"):
            if st.button("Save Plan to Account"):
                save_plan_to_db(df)

    
elif build_btn:
    st.warning("Please select a valid major to continue.")