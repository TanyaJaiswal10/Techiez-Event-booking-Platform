import streamlit as st
import api_client

def admin_dashboard():
    st.title("🛡️ Admin Dashboard")
    
    with st.sidebar:
        st.subheader("System Setup")
        if st.button("🚀 Seed Sample Data"):
            res = api_client.seed_db()
            if "message" in res:
                st.success(res["message"])
                st.rerun()
            else:
                st.error(res.get("detail", "Seeding failed"))

    st.subheader("Manage Venues & Events")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Venues", "Events", "All System Events", "Manage Organizers"])
    
    with tab1:
        with st.expander("Add New Venue"):
            name = st.text_input("Venue Name")
            city = st.text_input("City")
            capacity = st.number_input("Total Capacity", min_value=1)
            address = st.text_input("Address")
            if st.button("Save Venue"):
                res = api_client.add_venue({"name": name, "city": city, "total_capacity": capacity, "address": address})
                st.success(f"Venue added with ID: {res.get('id')}")
                st.rerun()
        
        st.write("### Existing Venues")
        venues = api_client.get_venues()
        if not venues or (isinstance(venues, dict) and "detail" in venues):
            st.info("No venues found. Create one above or use 'Seed Sample Data'.")
        else:
            for v in venues:
                st.markdown(f"**{v['name']}** ({v['city']}) - Capacity: {v['total_capacity']}")

    with tab2:
        with st.expander("Create New Event"):
            venues = api_client.get_venues()
            organizers = api_client.get_organizers()
            
            if not venues or not organizers or (isinstance(venues, dict) and "detail" in venues):
                st.warning("You need at least one Venue and one Organizer to create an event.")
            else:
                venue_options = {f"{v['name']} (ID: {v['id']})": v['id'] for v in venues}
                org_options = {}
                for o in organizers:
                    profile = api_client.get_organizer_profile(o['id'])
                    v_status = "✅" if (profile and profile.get('is_verified')) else "⏳"
                    label = f"{o['name']} ({v_status} {profile.get('specialization', 'No Spec') if profile else 'No Profile'})"
                    org_options[label] = o['id']
                
                sel_venue = st.selectbox("Select Venue", list(venue_options.keys()))
                sel_org = st.selectbox("Select Organizer (Vetted)", list(org_options.keys()))
                e_name = st.text_input("Event Name")
                cat = st.selectbox("Category", ["Music", "Sports", "Tech", "Other"])
                price = st.number_input("Price (₹)", min_value=0.0, value=500.0)
                max_t = st.number_input("Max Tickets Per User", min_value=1, value=4)
                date = st.date_input("Event Date")
                
                if st.button("Create Event"):
                    dt_str = f"{date}T18:00:00"
                    res = api_client.add_event({
                        "venue_id": venue_options[sel_venue], 
                        "organizer_id": org_options[sel_org], 
                        "name": e_name,
                        "category": cat, "event_date": dt_str, "ticket_price": price,
                        "max_tickets_per_user": max_t
                    })
                    if "id" in res:
                        st.success(f"Event '{e_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error(res.get("detail", "Failed to create event"))
    
    with tab3:
        st.subheader("Global Event List")
        all_e = api_client.get_all_events()
        if not all_e or (isinstance(all_e, dict) and "detail" in all_e):
            st.info("No events found in the system.")
        else:
            for e in all_e:
                st.markdown(f"**{e['name']}** | Org ID: {e['organizer_id']} | Status: {e['status']}")
    
    with tab4:
        st.subheader("Organizer Vetting")
        orgs = api_client.get_organizers()
        if not orgs:
            st.info("No organizers found.")
        else:
            for o in orgs:
                prof = api_client.get_organizer_profile(o['id'])
                with st.expander(f"{o['name']} ({o['email']})"):
                    if prof:
                        st.write(f"**Company**: {prof['company_name']}")
                        st.write(f"**Specialization**: {prof['specialization']}")
                        st.write(f"**Exp**: {prof['years_of_experience']} years")
                        st.write(f"**Bio**: {prof['bio']}")
                        if prof['is_verified']:
                            st.success("Verified Organizer")
                        else:
                            st.warning("Not Verified")
                            # We could add verification button here if needed
                    else:
                        st.info("No profile details provided yet.")

def organizer_dashboard():
    st.title("📅 Organizer Dashboard")
    
    st.subheader("Event Selection")
    my_events = api_client.get_my_events()
    
    if not my_events:
        st.info("No active events found for your account. Please ask the Admin to assign you an event.")
        return
    
    if isinstance(my_events, dict) and "detail" in my_events:
        st.error(f"Error fetching events: {my_events['detail']}")
        return

    event_options = {f"{e['name']} (ID: {e['id']})": e['id'] for e in my_events}
    selected_event_label = st.selectbox("Select Event to Manage", list(event_options.keys()))
    event_id = event_options[selected_event_label]

    st.divider()
    
    t1, t2, t3, t4 = st.tabs(["Seat Inventory", "Booking Summary", "Event Status", "Profile Settings"])
    
    with t1:
        st.subheader("Generate Seats")
        st.caption("Expand your event capacity up to the venue limit.")
        seat_count = st.number_input("Number of Seats to Add", min_value=1, value=50, key="seat_add_count")
        
        if st.button("Generate Seats", key="gen_btn"):
            res = api_client.create_seats(event_id, seat_count)
            if "message" in res:
                st.success(res["message"])
            else:
                st.error(res.get("detail", "Error creating seats"))
    
    with t2:
        st.subheader("Real-time Summary")
        if st.button("Refresh Metrics"):
            summary = api_client.get_event_summary(event_id)
            if "event_name" in summary:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Capacity", summary['total_seats'])
                col2.metric("Tickets Sold", summary['booked_seats'])
                col3.metric("Total Revenue", f"₹{summary['revenue']:.2f}")
                
                if summary['total_seats'] > 0:
                    occ = (summary['booked_seats'] / summary['total_seats']) * 100
                    st.progress(summary['booked_seats'] / summary['total_seats'], text=f"Occupancy: {occ:.1f}%")
            else:
                st.error(summary.get("detail", "Error fetching summary"))
    
    with t3:
        st.subheader("Manage Bookings")
        st.warning("Closing bookings will stop new users from selecting seats for this event.")
        if st.button("Close Bookings Permanently", type="primary"):
            res = api_client.close_event_bookings(event_id)
            if "message" in res:
                st.success("Bookings closed successfully.")
            else:
                st.error(res.get("detail", "Failed to close bookings"))
    
    with t4:
        st.subheader("Organizer Profile")
        profile = api_client.get_my_profile()
        
        with st.form("profile_form"):
            name = st.text_input("Company/Individual Name", value=profile.get("company_name", ""))
            bio = st.text_area("Biography", value=profile.get("bio", ""))
            exp = st.number_input("Years of Experience", min_value=0, value=profile.get("years_of_experience", 0))
            spec = st.text_input("Specialization", value=profile.get("specialization", ""))
            
            if st.form_submit_button("Update Profile"):
                res = api_client.update_profile({
                    "company_name": name,
                    "bio": bio,
                    "years_of_experience": exp,
                    "specialization": spec
                })
                if "message" in res:
                    st.success("Profile updated!")
                    st.rerun()
                else:
                    st.error(res.get("detail", "Update failed"))
        
        if profile.get("is_verified"):
            st.success("✅ Your profile is verified.")
        else:
            st.warning("⚠️ Profile not verified yet.")
