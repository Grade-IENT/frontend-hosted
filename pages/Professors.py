import streamlit as st
import pandas as pd
import psycopg2
from streamlit_searchbox import st_searchbox
from fuzzywuzzy import process

st.set_page_config(page_title= "Gradient - Professors", page_icon=":tada:", layout ="wide", initial_sidebar_state="collapsed")
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
# use CSS
def local_css(file_name):
    with open(file_name) as f :
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style/style.css")


with st.container():
     st.write("Go to :")
     left, middle, right = st.columns(3)
     with middle:          
        if st.button("Four Year Plan", use_container_width= True):
            st.switch_page("pages/Four_Year_Plan.py")
    
     with left:

        if st.button("Profile", use_container_width= True):
            st.switch_page("pages/Profile.py")

     with right:
        if st.button("Scheduling", use_container_width=True):
            st.switch_page("pages/Schedule.py")

     st.write("---")

# def get_connection():
#     return psycopg2.connect(
#         host="localhost",
#         database="gradientdb",
#         user="postgres",  
#         password="1234"  # Replace with your password
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
    @st.cache_data(ttl=600)  # cache for 10 minutes
    def load_professors():
        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT prof_name, netid, metrics, SQI, summary
        FROM professor
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return pd.DataFrame(rows, columns=["Professor Name", "NetID", "Metrics", "SQI", "Summary"])

    st.title("Professor Lookup")
    image_column, search_column = st.columns((1,9))

    with image_column:
        st.image("search.png", caption= None, width= 100)

    with search_column:     
        df = load_professors()
        prof_names = df["Professor Name"].tolist()

        def search_professors(search_term: str):
            if not search_term:
                return []
            return [name for name, _ in process.extract(search_term, prof_names, limit=5)]
        
        if len(df.index) != 0:
            selected_prof = st_searchbox(search_professors, placeholder="Search for a Professor...")

            selected_prof_data = df[df["Professor Name"] == selected_prof]

            for _, row in selected_prof_data.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background-color:#ffffff; padding:20px; border-radius:12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom:20px;">

                    <h4 style="margin-bottom: 10px;">{row['Professor Name']}</h4>

                    <p style="margin: 6px 0;"><strong>NetID:</strong> {row['NetID'] or 'N/A'}</p>
                    <p style="margin: 6px 0;"><strong>Metrics:</strong> {row['Metrics']:.2f}</p>
                    <p style="margin: 6px 0;"><strong>SQI:</strong> {row['SQI'] or 'N/A'}</p>

                    <div style="margin-top: 15px; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #bbb; border-radius: 8px;">
                        <p style="margin: 0 0 10px;"><strong>Professor Summary:</strong></p>
                        <p style="margin: 0; font-style: italic; color: #333;">{row['Summary']}</p>
                    </div>

                    <div style="font-size: 0.85em; color: #666; background-color: #f0f0f0; padding: 8px; border-radius: 6px; margin-top: 10px;">
                        ⚠️ <em>Summaries are generated by AI and may not be 100% accurate.</em>
                    </div>

                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No professors found.")

# with st.container():

#     st.title("Professor Lookup")
#     image_column, search_column = st.columns((1,9))

#     with image_column:
#         st.image("search.png", caption= None, width= 100)

#     with search_column:
#         prof = st.text_input("Search up your professors and find their ratings!")
#         if prof:
#             st.write("You searched Professor:", prof)

#             conn = get_connection()
#             cur = conn.cursor()


#             query = """
#             SELECT prof_name, netid, metrics, SQI, summary
#             FROM professor
#             WHERE LOWER(prof_name) LIKE %s
#             """
#             cur.execute(query, (f"%{prof.lower()}%",))
#             rows = cur.fetchall()

#             if rows:
#                 df = pd.DataFrame(rows, columns=["Professor Name", "NetID", "Metrics", "SQI", "Summary"])
#                 print(rows)
#                 for _, row in df.iterrows():
#                     with st.container():
#                         st.markdown(f"""
#                         <div style="background-color:#f5f5f5;padding:15px;border-radius:10px;margin-bottom:10px">
#                         <h5>{row['Professor Name']}</h5>
#                         <p><strong>NetID:</strong> {row['NetID'] or 'N/A'}  
#                         <br><strong>Metrics:</strong> {row['Metrics']:.2f}  
#                         <br><strong>SQI:</strong> {row['SQI'] or 'N/A'}  
#                         <br><strong>Summary:</strong> {row['Summary']}</p>
#                         </div>
#                         """, unsafe_allow_html=True)
#             else:
#                 st.warning("No professors found matching that name.")

#             cur.close()
#             conn.close()
