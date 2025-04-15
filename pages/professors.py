import streamlit as st
import pandas as pd
import psycopg2

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
            st.switch_page("pages/four_year.py")
    
     with left:

        if st.button("Profile", use_container_width= True):
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

    st.title("Professor Lookup")
    image_column, search_column = st.columns((1,9))

    with image_column:
        st.image("search.png", caption= None, width= 100)

    with search_column:
        # st.write("You searched Professor:", prof)

        conn = get_connection()
        cur = conn.cursor()


        query = """
        SELECT prof_name, netid, metrics, SQI, summary
        FROM professor
        """
        cur.execute(query)
        rows = cur.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=["Professor Name", "NetID", "Metrics", "SQI", "Summary"])
            prof_names = df["Professor Name"].tolist()

            # matches = process.extract(prof.lower(), prof_names, limit=1000)

            # options = [match[0] for match in matches]
            selected_prof = st.selectbox("## Select a professor", prof_names)

            selected_prof_data = df[df["Professor Name"] == selected_prof]

            for _, row in selected_prof_data.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background-color:#f5f5f5;padding:15px;border-radius:10px;margin-bottom:10px">
                    <h5>{row['Professor Name']}</h5>
                    <p><strong>NetID:</strong> {row['NetID'] or 'N/A'}  
                    <br><strong>Metrics:</strong> {row['Metrics']:.2f}  
                    <br><strong>SQI:</strong> {row['SQI'] or 'N/A'}  
                    <br><strong>Summary:</strong> {row['Summary']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No professors found.")

        cur.close()
        conn.close()

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
