import streamlit as st
from api_client import get_cases, get_refunds, update_case_status, approve_refund

def support_dashboard():
    st.title("🎧 Support Representative")
    
    tab1, tab2 = st.tabs(["Active Cases", "Refund Requests"])
    
    with tab1:
        st.subheader("User Support Tickets")
        cases = get_cases()
        
        if not cases:
            st.info("No active support cases.")
        elif isinstance(cases, dict) and "detail" in cases:
            st.error(f"Error fetching cases: {cases['detail']}")
        else:
            for case in cases:
                with st.container():
                    st.markdown(f"""
                    <div class="card">
                        <b>Case #{case['id']}: {case['description'][:50]}...</b><br>
                        User ID: {case['raised_by']}<br>
                        Order ID: {case['order_id'] or 'N/A'}<br>
                        Status: <span style="color:{'orange' if case['status'] == 'open' else 'green'}">{case['status'].upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    new_status = st.selectbox("New Status", ["open", "resolved", "closed"], key=f"status_{case['id']}", index=["open", "resolved", "closed"].index(case['status']) if case['status'] in ["open", "resolved", "closed"] else 0)
                    notes = st.text_area("Resolution Notes", key=f"notes_{case['id']}", value=case.get('resolution_notes') or "")
                    
                    if st.button("Update Case", key=f"btn_{case['id']}"):
                        res = update_case_status(case['id'], new_status, notes)
                        if "message" in res:
                            st.success(f"Case {case['id']} updated!")
                            st.rerun()
                        else:
                            st.error(res.get("detail", "Update failed"))

    with tab2:
        st.subheader("Pending Refunds")
        refunds = get_refunds()
        
        if not refunds:
            st.info("No pending refund requests.")
        elif isinstance(refunds, dict) and "detail" in refunds:
            st.error(f"Error fetching refunds: {refunds['detail']}")
        else:
            for req in refunds:
                if req['status'] == 'pending':
                    with st.container():
                        st.markdown(f"""
                        <div class="card">
                            <b>Refund #{req['id']} for Order #{req['order_id']}</b><br>
                            Reason: {req['reason']}<br>
                            Requested At: {req.get('requested_at', 'N/A')}<br>
                            Status: <b>{req['status'].upper()}</b>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        if col1.button("Approve", key=f"app_{req['id']}"):
                            res = approve_refund(req['id'], True)
                            if "message" in res:
                                st.success(f"Refund {req['id']} approved!")
                                st.rerun()
                            else:
                                st.error(res.get("detail", "Approval failed"))
                                
                        if col2.button("Reject", key=f"rej_{req['id']}"):
                            res = approve_refund(req['id'], False)
                            if "message" in res:
                                st.warning(f"Refund {req['id']} rejected.")
                                st.rerun()
                            else:
                                st.error(res.get("detail", "Rejection failed"))
