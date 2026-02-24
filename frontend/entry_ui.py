import streamlit as st
from api_client import validate_ticket, mark_used

def entry_dashboard():
    st.title("🛂 Entry Management")
    st.subheader("Scan / Validate Tickets")
    
    code = st.text_input("Enter Ticket Code")
    if st.button("Validate"):
        res = validate_ticket(code)
        if "ticket_id" in res:
            st.success(res["message"])
            if st.button(f"Mark Ticket #{res['ticket_id']} as USED"):
                use_res = mark_used(res["ticket_id"])
                st.info(use_res["message"])
        else:
            st.error(res.get("detail", "Invalid code"))
