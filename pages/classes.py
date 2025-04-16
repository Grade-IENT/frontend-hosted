import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Gradient - Classes", page_icon=":tada:", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        div[data-testid="collapsedControl"] {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True
)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

# Navigation buttons
with st.container():
    st.write("Go to :")
    left, middle, right = st.columns(3)
    with middle:
        if st.button("Four Year Plan", use_container_width=True):
            st.switch_page("pages/four_year.py")
    with left:
        if st.button("Profile", use_container_width=True):
            st.switch_page("pages/profile.py")
    with right:
        if st.button("Scheduling", use_container_width=True):
            st.switch_page("pages/schedule.py")
    st.write("---")

# def get_connection():
#     return psycopg2.connect(
#         host="localhost",
#         database="gradientdb",
#         user="postgres",  
#         # password="yourpassword"  # Optional
#     )
def get_connection():
    return psycopg2.connect(
        host=st.secrets["db_host"],
        port=st.secrets["db_port"],
        dbname=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

with st.container():
    st.title("Class Lookup")
    image_column, search_column = st.columns((1, 9))

    with image_column:
        st.image("search.png", caption=None, width=100)

    with search_column:
        search_term = st.text_input("Search for a class by name or course code:")

        if search_term:
            st.write("You searched for class:", search_term)

            conn = get_connection()
            cur = conn.cursor()

            query = """
            SELECT c.course_code, c.course_name, 
                   pre.course_name AS pre_req_name, 
                   co.course_name AS co_req_name,
                   c.SQI
            FROM Class c
            LEFT JOIN Class pre ON c.pre_req_group = pre.id
            LEFT JOIN Class co ON c.co_req = co.id
            WHERE LOWER(c.course_code) LIKE %s OR LOWER(c.course_name) LIKE %s
            """
            cur.execute(query, (f"%{search_term.lower()}%", f"%{search_term.lower()}%"))
            rows = cur.fetchall()

            if rows:
                df = pd.DataFrame(rows, columns=["Course Code", "Course Name", "Pre-requisite", "Co-requisite", "SQI"])
                for _, row in df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color:#f5f5f5;padding:15px;border-radius:10px;margin-bottom:10px">
                        <h5>{row['Course Code']} - {row['Course Name']}</h5>
                        <p><strong>Pre-req:</strong> {row['Pre-requisite'] or 'None'}  
                        <br><strong>Co-req:</strong> {row['Co-requisite'] or 'None'}  
                        <br><strong>SQI:</strong> {row['SQI'] if pd.notnull(row['SQI']) else 'N/A'}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No classes found matching your query.")

            cur.close()
            conn.close()