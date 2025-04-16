import streamlit as st
import pandas as pd
from pathlib import Path
import sys

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
    "Electrical Engineering":               "electrical_engineering_courses.csv",
    "Industrial and Systems Engineering":    "industrial_systems_engineering_courses.csv",
    "Materials Science Engineering":         "materials_science_engineering_courses.csv",
    "Mechanical Engineering":                "mechanical_engineering_courses.csv",
    "Packaging Engineering":                "packaging_engineering_courses.csv",
}

# ─────────────── Page setup ───────────────
st.set_page_config(page_title="Gradient – Four‑Year Plan", page_icon=":tada:", layout="wide", initial_sidebar_state="collapsed")

# ─────────────── Style Injection ───────────────
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

# Additional inline fixes
st.markdown("""
<style>
/* Hide sidebar toggle */
div[data-testid="collapsedControl"] {
    visibility: hidden;
}

/* AP slider box */
div[data-baseweb="slider"] {
    background-color: white !important;
    color: black !important;
    border-radius: 6px;
    padding: 8px;
}

/* Replace green success msg */
div[data-testid="stMarkdownContainer"] > div[style*="background-color: rgb(220, 252, 231)"] {
    background-color: transparent !important;
    color: black !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Streamlit's AP slider container */
div[data-baseweb="slider"] {
    background-color: white !important;
    padding: 10px;
    border-radius: 8px;
}

/* WebKit slider track + thumb */
input[type="range"] {
    accent-color: black !important;
}

/* Ensure labels (1–5) are black */
div[data-baseweb="slider"] span {
    color: black !important;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.write("Go to:")
    left, middle, right = st.columns(3)
    with left:
        if st.button("Profile", use_container_width=True):
            st.switch_page("pages/profile.py")
    with middle:
        if st.button("Professors", use_container_width=True):
            st.switch_page("pages/professors.py")
    with right:
        if st.button("Scheduling", use_container_width=True):
            st.switch_page("pages/schedule.py")
    st.write("---")

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

build_btn = st.button("Generate Plan")

# ─────────────── Generate Plan ───────────────
if build_btn and major in majors:
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
                # Parse each row into structured columns
                raw_rows = df[sem_name].replace("", pd.NA).dropna().tolist()

                parsed = []
                for entry in raw_rows:
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
                    except Exception as e:
                        # fallback: include unparsed string
                        parsed.append({
                            "Course Code": "",
                            "Course Name": entry.strip(),
                            "Credits": "",
                            "SQI": ""
                        })

                # Display structured table
                parsed_df = pd.DataFrame(parsed)
                parsed_df.columns = ["Course_Code", "Course_Name", "Credits", "SQI"]

                st.markdown(f"**{sem_name}** — Total Credits: **{sem_credits[sem_idx]}**")

                valid_sqis = [row["SQI"] for row in parsed if isinstance(row["SQI"], float)]
                if valid_sqis:
                    avg_sqi = sum(valid_sqis) / len(valid_sqis)
                    st.markdown(f"Average SQI: **{avg_sqi:.2f}**")
                else:
                    st.markdown("Average SQI: **N/A**")

                parsed_df = pd.DataFrame(parsed, index=None)
                parsed_df.columns = ["Course Code", "Course Name", "Credits", "SQI"]

                # Prevent word wrapping in table headers and cells
                st.markdown("""
                <style>
                thead tr th, tbody tr td {
                    white-space: nowrap !important;
                    text-align: left !important;
                }
                thead tr th:nth-child(3),
                thead tr th:nth-child(4),
                tbody tr td:nth-child(3),
                tbody tr td:nth-child(4) {
                    text-align: center !important;
                }
                </style>
                """, unsafe_allow_html=True)

                st.dataframe(parsed_df.style.hide(axis="index"), hide_index = True,use_container_width=True)

    st.download_button("Download Plan as CSV",
                       data=df.to_csv(index=False).encode(),
                       file_name="four_year_plan.csv")

elif build_btn:
    st.warning("Please select a valid major to continue.")
