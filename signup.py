import streamlit as st
import firebase
import app

def login_page():
    """Streamlit login and signup page"""
    st.title("Veda VisionGPT - Register/Login")
    
    firebase.initialize_firebase()
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login_email and login_password:
                user = firebase.login(login_email, login_password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.success("Login Successful!")
                    st.experimental_rerun()
                else:
                    st.error("Login Failed")
            else:
                st.warning("Please enter email and password")
        
        if st.button("Forgot Password"):
            reset_email = st.text_input("Enter your email to reset password")
            if reset_email:
                reset_link = firebase.reset_password(reset_email)
                if reset_link:
                    st.info("Password reset link generated. Check your email.")
    
    with tab2:
        st.header("Sign Up")
        signup_name = st.text_input("Full Name", key="signup_name")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Sign Up"):
            if signup_password == confirm_password:
                if signup_name and signup_email and signup_password:
                    user = firebase.signup(signup_email, signup_password, signup_name)
                    if user:
                        st.success("Account created successfully!")
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.experimental_rerun()
                else:
                    st.warning("Please fill in all fields")
            else:
                st.error("Passwords do not match")

def main():
    if not hasattr(st.session_state, 'logged_in') or not st.session_state.logged_in:
        login_page()
    else:
        app.main()

if __name__ == '__main__':
    main()