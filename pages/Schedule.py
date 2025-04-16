import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title= "Gradient - Scheduling", page_icon=":tada:", layout ="wide", initial_sidebar_state="collapsed")
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
    
     with right:

        if st.button("Professors", use_container_width= True):
            st.switch_page("pages/Professors.py")

     with left:
        if st.button("Profile", use_container_width=True):
            st.switch_page("pages/Profile.py")
     st.write("---")



#HEADER
with st.container():
    st.subheader("Here is your")
    st.title("Schedule")
    ##st.write("[click here](https://www.google.com/search?q=oscars+2025&rlz=1C1ONGR_enUS1032US1032&oq=oscars+2025&gs_lcrp=EgZjaHJvbWUqDQgAEAAYgwEYsQMYgAQyDQgAEAAYgwEYsQMYgAQyDQgBEAAYgwEYsQMYgAQyDQgCEAAYgwEYsQMYgAQyDQgDEAAYgwEYsQMYgAQyDQgEEAAYgwEYsQMYgAQyDQgFEAAYgwEYsQMYgAQyDQgGEAAYgwEYsQMYgAQyDQgHEAAYgwEYsQMYgAQyEAgIEAAYgwEYsQMYgAQYigUyEAgJEAAYgwEYsQMYgAQYigXSAQgyMjI5ajBqN6gCALACAA&sourceid=chrome&ie=UTF-8)")


