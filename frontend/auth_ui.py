import streamlit as st
from api_client import login, signup

def login_section():
    st.header("Eventora - Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        res = login(email, password)
        if "access_token" in res:
            st.session_state["token"] = res["access_token"]
            st.session_state["role"] = res["role"]
            st.session_state["user_email"] = email
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error(res.get("detail", "Login failed"))

def signup_section():
    st.header("Eventora - Register")
    name = st.text_input("Full Name")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_pass")
    role = st.selectbox("Role", ["customer", "organizer", "admin", "entry_manager", "support"])
    if st.button("Sign Up"):
        res = signup(name, email, password, role)
        if "user_id" in res:
            st.success("Account created! Please login.")
        else:
            st.error(res.get("detail", "Signup failed"))
