import streamlit as st

st.set_page_config(page_title= "Gradient", page_icon=":tada:", layout ="wide", initial_sidebar_state="collapsed")
 

# use CSS
with open('./style/style.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

#HEADER
with st.container():
    left, right = st.columns((5,1))

    with left:
        st.subheader("Hi,")
        st.title("Welcome to Grade-ient!")
        st.write("Grade-ient is your one-stop shop for scheduling, prereqs, professors and 4 year plans!")
        #st.write("[click here](https://www.google.com/search?q=oscars+2025&rlz=1C1ONGR_enUS1032US1032&oq=oscars+2025&gs_lcrp=EgZjaHJvbWUqDQgAEAAYgwEYsQMYgAQyDQgAEAAYgwEYsQMYgAQyDQgBEAAYgwEYsQMYgAQyDQgCEAAYgwEYsQMYgAQyDQgDEAAYgwEYsQMYgAQyDQgEEAAYgwEYsQMYgAQyDQgFEAAYgwEYsQMYgAQyDQgGEAAYgwEYsQMYgAQyDQgHEAAYgwEYsQMYgAQyEAgIEAAYgwEYsQMYgAQYigUyEAgJEAAYgwEYsQMYgAQYigXSAQgyMjI5ajBqN6gCALACAA&sourceid=chrome&ie=UTF-8)")
    with right: 
        st.image("redcap.jpg", width= 150)


#--log in ------
with st.container():
    st.write("---")
    st.header("LOG IN:")

    contact_form = """
    <form action="https://formsubmit.co/insiyachitalwala@gmail.com" method="POST">
        <input type = "hidden" name = "_captcha" value="false">
        <input type="email" name="email" placeholder= "Email" required>
        <input type="text" name="password" placeholder="Password" required>
        
    </form>
    """

#        <textarea name = "message" placeholder="your message here" required></textarea>



    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown(contact_form,unsafe_allow_html=True)
        if st.button("Log In:"):
            st.switch_page("pages/profile.py")
    with right_column: 
        st.empty()
