import streamlit as st
from api_client import get_events, get_available_seats, place_order, confirm_payment, get_my_tickets, raise_support_case, request_refund, create_razorpay_order_api, verify_razorpay_payment_api


def customer_dashboard():
    st.title("🎟️ Online Event Booking")
    
    tab1, tab2, tab3 = st.tabs(["Browse Events", "My Tickets", "Support"])
    
    with tab1:
        st.header("Upcoming Events")
        events = get_events()
        if not events:
            st.info("No upcoming events found.")
        
        for ev in events:
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h3>{ev['name']}</h3>
                    <p>Category: {ev['category']} | Date: {ev['event_date']}</p>
                    <p>Price: <b>₹{ev['ticket_price']}</b></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Book Seats for {ev['name']}", key=f"btn_{ev['id']}"):
                    st.session_state["selected_event"] = ev
                    st.session_state["booking_step"] = "seats"
        
        if "booking_step" in st.session_state and st.session_state["booking_step"] == "seats":
            st.divider()
            ev = st.session_state["selected_event"]
            st.subheader(f"Select Seats for {ev['name']}")
            seats = get_available_seats(ev['id'])
            
            if not seats:
                st.warning("No seats generated for this event yet.")
            else:
                booked_count = sum(1 for s in seats if s['status'] == 'booked')
                total_count = len(seats)
                st.write(f"📊 Capacity: {total_count} | Booked: {booked_count} | Available: {total_count - booked_count}")
                
                st.write("### Seating Map")
                st.caption("🟩 Available | 🟥 Booked")
                
                selected_seat_ids = []
                # 10 columns grid
                row_cols = st.columns(10)
                for i, s in enumerate(seats):
                    col = row_cols[i % 10]
                    if s['status'] == 'booked':
                        col.button(f"🚫 {s['seat_number']}", key=f"seat_{s['id']}", disabled=True)
                    else:
                        if col.checkbox(f"💺 {s['seat_number']}", key=f"seat_cb_{s['id']}"):
                            selected_seat_ids.append(s['id'])
                
                if st.button("Proceed to Pay"):
                    res = place_order(ev['id'], selected_seat_ids)
                    if "order_id" in res:
                        st.session_state["pending_order"] = res
                        st.session_state["selected_seat_ids"] = selected_seat_ids
                        st.session_state["booking_step"] = "payment"
                        st.rerun()
                    else:
                        st.error(res.get("detail", "Order failed"))

        if "booking_step" in st.session_state and st.session_state["booking_step"] == "payment":
            st.divider()
            order_info = st.session_state["pending_order"]
            seat_ids = st.session_state["selected_seat_ids"]
            st.subheader("💳 Complete Payment")
            st.write(f"Order ID: {order_info['order_id']}")
            st.write(f"Total Amount: ₹{order_info['total_amount']}")
            
            pay_method = st.radio("Select Payment Method", ["Simulation (Fast)", "Razorpay (Test Mode)"])
            
            if pay_method == "Simulation (Fast)":
                if st.button("Confirm Simulation Payment"):
                    pay_res = confirm_payment(order_info['order_id'], seat_ids)
                    if "message" in pay_res:
                        st.success("Booking confirmed! Check 'My Tickets'.")
                        del st.session_state["booking_step"]
                        st.rerun()
                    else:
                        st.error("Payment failed.")
            
            else:
                st.info("In a real application, the Razorpay popup would appear here. For this demo, please click the button below to generate a Razorpay Order ID and then simulate the success callback.")
                
                if st.button("Generate Razorpay Order"):
                    rzp_res = create_razorpay_order_api(order_info['order_id'])
                    if "razorpay_order_id" in rzp_res:
                        st.session_state["rzp_order_id"] = rzp_res["razorpay_order_id"]
                        st.success(f"Razorpay Order Created: {rzp_res['razorpay_order_id']}")
                    else:
                        st.error("Failed to create Razorpay order.")
                
                if "rzp_order_id" in st.session_state:
                    st.write("---")
                    st.caption("Simulate Razorpay Success Callback")
                    payment_id = st.text_input("Razorpay Payment ID", value="pay_test_123")
                    signature = st.text_input("Razorpay Signature", value="sig_test_123")
                    
                    if st.button("Verify & Complete"):
                        verify_data = {
                            "razorpay_order_id": st.session_state["rzp_order_id"],
                            "razorpay_payment_id": payment_id,
                            "razorpay_signature": signature,
                            "seat_ids": seat_ids
                        }
                        verify_res = verify_razorpay_payment_api(order_info['order_id'], verify_data)
                        if "message" in verify_res:
                            st.success("Payment verified! Ticket generated.")
                            del st.session_state["booking_step"]
                            del st.session_state["rzp_order_id"]
                            st.rerun()
                        else:
                            st.error(verify_res.get("detail", "Verification failed. (Note: Signature verification will fail if not using real keys)"))

    with tab2:
        st.header("Your Tickets")
        tickets = get_my_tickets()
        if not tickets:
            st.info("You haven't booked any tickets yet.")
        for t in tickets:
            st.markdown(f"""
            <div class="card">
                <b>Ticket Code: {t['ticket_code']}</b><br>
                Order ID: {t['order_id']}<br>
                Status: {t['status'].capitalize()}<br>
                Seat: {t['seat_id']}
            </div>
            """, unsafe_allow_html=True)
            
    with tab3:
        st.header("Support & Refunds")
        with st.form("support_form"):
            s_order_id = st.number_input("Order ID (Optional)", step=1, value=0, help="Enter the Order ID related to your issue. You can find this in the 'My Tickets' tab.")
            desc = st.text_area("Issue Description")
            if st.form_submit_button("Raise Case"):
                order_val = s_order_id if s_order_id > 0 else None
                res = raise_support_case(order_val, desc)
                st.success(res.get("message", "Case raised"))
        
        st.divider()
        st.subheader("Refund Request")
        with st.form("refund_form"):
            r_order_id = st.number_input("Order ID", step=1, help="Enter the Order ID you wish to refund. You can find this in the 'My Tickets' tab.")
            reason = st.text_input("Reason")
            if st.form_submit_button("Submit Refund Request"):
                res = request_refund(r_order_id, reason)
                if "message" in res:
                    st.success(res['message'])
                else:
                    st.error(res.get("detail", "Request failed"))
