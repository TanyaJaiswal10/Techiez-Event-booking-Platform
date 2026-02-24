import streamlit as st
from auth_ui import login_section, signup_section
from customer_ui import customer_dashboard
from admin_ui import admin_dashboard, organizer_dashboard
from entry_ui import entry_dashboard
from support_ui import support_dashboard

st.set_page_config(page_title="Ticket Booking Platform", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for "Wowed" design
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #6c63ff;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #554dec;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
    }
    .card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

def logout():
    st.session_state["token"] = None
    st.session_state["role"] = None
    st.session_state["user_email"] = None
    st.rerun()

if not st.session_state["token"]:
    tab1, tab2 = st.tabs(["Login", "Signup"])
    with tab1:
        login_section()
    with tab2:
        signup_section()
else:
    st.sidebar.title(f"Welcome, {st.session_state['user_email']}")
    st.sidebar.write(f"Role: **{st.session_state['role'].capitalize()}**")
    
    if st.sidebar.button("Logout"):
        logout()
    
    role = st.session_state["role"]
    if role == "admin":
        admin_dashboard()
    elif role == "organizer":
        organizer_dashboard()
    elif role == "customer":
        customer_dashboard()
    elif role == "entry_manager":
        entry_dashboard()
    elif role == "support":
        support_dashboard()
