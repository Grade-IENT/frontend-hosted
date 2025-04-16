import streamlit as st

st.set_page_config(page_title= "Gradient - Your Profile", page_icon=":tada:", layout ="wide", initial_sidebar_state="collapsed")
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


#HEADER
with st.container():
    st.title("Your Profile")

    info, picture = st.columns((5,2))
    with info: 
        st.write("---")
        st.write("Intended Major: Undecided")
        st.write("Completed Credits: 31")
        st.write("GPA: N/A ")



    with picture:
        st.image("blankprofilepic.jpg", caption= "Profile Picture", width= 200)

   

with st.container():
     
     st.write("Go to :")
     left, middle, right = st.columns(3)
     with left:          
        if st.button("Four Year Plan", use_container_width= True):
            st.switch_page("pages/Four_Year_Plan.py")
    
     with middle:

        if st.button("Professors", use_container_width= True):
            st.switch_page("pages/Professors.py")

     with right:
        if st.button("Scheduling", use_container_width=True):
            st.switch_page("pages/Schedule.py")
    
    
     st.write("---")


        