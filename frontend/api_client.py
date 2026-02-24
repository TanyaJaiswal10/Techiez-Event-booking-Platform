import requests
import streamlit as st

BASE_URL = "http://localhost:8000"

def signup(name, email, password, role):
    response = requests.post(f"{BASE_URL}/signup", json={"name": name, "email": email, "password": password, "role": role})
    return response.json()


def login(email, password):
    response = requests.post(f"{BASE_URL}/token", data={"username": email, "password": password})
    return response.json()

def get_headers():
    if "token" in st.session_state:
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}

def handle_response(response):
    try:
        return response.json()
    except Exception:
        return {"detail": f"API Error {response.status_code}: {response.text[:100]}"}

# Admin APIs
def add_venue(data):
    return handle_response(requests.post(f"{BASE_URL}/admin/venues", json=data, headers=get_headers()))

def add_event(data):
    return handle_response(requests.post(f"{BASE_URL}/admin/events", json=data, headers=get_headers()))

def get_all_events():
    return handle_response(requests.get(f"{BASE_URL}/admin/events/all", headers=get_headers()))

def get_venues():
    return handle_response(requests.get(f"{BASE_URL}/admin/venues", headers=get_headers()))

def get_organizers():
    return handle_response(requests.get(f"{BASE_URL}/admin/organizers", headers=get_headers()))

def seed_db():
    return handle_response(requests.post(f"{BASE_URL}/admin/seed", headers=get_headers()))

# Organizer APIs
def create_seats(event_id, count):
    return handle_response(requests.post(f"{BASE_URL}/organizer/events/{event_id}/seats", params={"seat_count": count}, headers=get_headers()))

def get_my_events():
    return handle_response(requests.get(f"{BASE_URL}/organizer/events/me", headers=get_headers()))

def get_event_summary(event_id):
    return handle_response(requests.get(f"{BASE_URL}/organizer/events/{event_id}/summary", headers=get_headers()))

def close_event_bookings(event_id):
    return handle_response(requests.patch(f"{BASE_URL}/organizer/events/{event_id}/close", headers=get_headers()))

def get_my_profile():
    return handle_response(requests.get(f"{BASE_URL}/organizer/profile/me", headers=get_headers()))

def update_profile(data):
    return handle_response(requests.post(f"{BASE_URL}/organizer/profile/update", json=data, headers=get_headers()))

def get_organizer_profile(org_id):
    return handle_response(requests.get(f"{BASE_URL}/admin/organizers/{org_id}/profile", headers=get_headers()))

# Customer APIs
def get_events():
    return handle_response(requests.get(f"{BASE_URL}/customer/events", headers=get_headers()))

def get_available_seats(event_id):
    return handle_response(requests.get(f"{BASE_URL}/customer/events/{event_id}/seats", headers=get_headers()))

def place_order(event_id, seat_ids, offer_code=None):
    return handle_response(requests.post(f"{BASE_URL}/customer/orders", json={"event_id": event_id, "seat_ids": seat_ids, "offer_code": offer_code}, headers=get_headers()))

def confirm_payment(order_id, seat_ids):
    return handle_response(requests.post(f"{BASE_URL}/customer/orders/{order_id}/confirm_payment", json={"seat_ids": seat_ids}, headers=get_headers()))

def create_razorpay_order_api(order_id):
    return handle_response(requests.post(f"{BASE_URL}/customer/orders/{order_id}/create-razorpay-order", headers=get_headers()))

def verify_razorpay_payment_api(order_id, razorpay_data):
    return handle_response(requests.post(f"{BASE_URL}/customer/orders/{order_id}/verify-razorpay-payment", json=razorpay_data, headers=get_headers()))

def get_my_tickets():
    return handle_response(requests.get(f"{BASE_URL}/customer/tickets", headers=get_headers()))

# Entry APIs
def validate_ticket(code):
    return handle_response(requests.post(f"{BASE_URL}/entry/validate/{code}", headers=get_headers()))

def mark_used(ticket_id):
    return handle_response(requests.patch(f"{BASE_URL}/entry/tickets/{ticket_id}/use", headers=get_headers()))

# Support APIs
def get_cases():
    return handle_response(requests.get(f"{BASE_URL}/support/cases", headers=get_headers()))

def update_case_status(case_id, status, notes):
    return handle_response(requests.patch(f"{BASE_URL}/support/cases/{case_id}", json={"status": status, "notes": notes}, headers=get_headers()))

def get_refunds():
    return handle_response(requests.get(f"{BASE_URL}/support/refunds", headers=get_headers()))

def approve_refund(refund_id, approve: bool):
    return handle_response(requests.post(f"{BASE_URL}/support/refunds/{refund_id}/approve", json={"approve": approve}, headers=get_headers()))

def raise_support_case(order_id, description):
    return handle_response(requests.post(f"{BASE_URL}/customer/support", json={"order_id": order_id, "description": description}, headers=get_headers()))

def request_refund(order_id, reason):
    return handle_response(requests.post(f"{BASE_URL}/customer/refunds", json={"order_id": order_id, "reason": reason}, headers=get_headers()))
