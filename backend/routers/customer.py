from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Event, Seat, UserRole, Order, Ticket, RefundRequest, SupportCase, Offer, EventStatus, OrderStatus, TicketStatus
from ..auth import RoleChecker, get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from ..payment_utils import create_razorpay_order, verify_payment_signature

router = APIRouter(prefix="/customer", tags=["customer"])
customer_only = RoleChecker([UserRole.CUSTOMER])

class OrderCreate(BaseModel):
    event_id: int
    seat_ids: List[int]
    offer_code: Optional[str] = None

class RefundRequestCreate(BaseModel):
    order_id: int
    reason: str

class SupportCaseCreate(BaseModel):
    order_id: Optional[int] = None
    description: str

@router.get("/events")
def view_upcoming_events(db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.status == EventStatus.UPCOMING).all()

@router.get("/events/{event_id}/seats")
def view_event_seats(event_id: int, db: Session = Depends(get_db)):
    return db.query(Seat).filter(Seat.event_id == event_id).all()

@router.post("/orders")
def place_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user = Depends(customer_only)):
    event = db.query(Event).filter(Event.id == order_data.event_id).first()
    if not event or event.status != EventStatus.UPCOMING:
        raise HTTPException(status_code=400, detail="Event not available for booking")
    
    if len(order_data.seat_ids) > event.max_tickets_per_user:
        raise HTTPException(status_code=400, detail=f"Cannot book more than {event.max_tickets_per_user} tickets")
    
    # Check if user already has tickets for this event
    existing_orders = db.query(Order).filter(Order.user_id == current_user.id, Order.event_id == order_data.event_id, Order.order_status == OrderStatus.CONFIRMED).all()
    # Simplified check: total seats in confirmed orders
    total_existing_seats = 0
    for o in existing_orders:
        total_existing_seats += db.query(Ticket).filter(Ticket.order_id == o.id).count()
    
    if total_existing_seats + len(order_data.seat_ids) > event.max_tickets_per_user:
         raise HTTPException(status_code=400, detail="Total tickets exceed limit for this user")

    # Double booking protection (locking seats)
    seats = db.query(Seat).filter(Seat.id.in_(order_data.seat_ids), Seat.status == "available").all()
    if len(seats) != len(order_data.seat_ids):
        raise HTTPException(status_code=400, detail="Some seats are already booked or invalid")
    
    total_amount = event.ticket_price * len(order_data.seat_ids)
    
    # Apply offer
    if order_data.offer_code:
        offer = db.query(Offer).filter(Offer.code == order_data.offer_code, Offer.event_id == order_data.event_id).first()
        if offer and offer.used_count < offer.max_uses and offer.valid_until > datetime.now():
            total_amount -= (total_amount * offer.discount_percent / 100)
            offer.used_count += 1
    
    new_order = Order(
        user_id=current_user.id,
        event_id=order_data.event_id,
        total_amount=total_amount,
        payment_mode="simulation",
        order_status=OrderStatus.PENDING
    )
    db.add(new_order)
    db.flush() # Get order ID
    
    # Reserve seats
    for seat in seats:
        seat.status = "booked"
    
    db.commit()
    return {"message": "Order created", "order_id": new_order.id, "total_amount": total_amount}

class RazorpayOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int
    currency: str

@router.post("/orders/{order_id}/create-razorpay-order", response_model=RazorpayOrderResponse)
def get_razorpay_order(order_id: int, db: Session = Depends(get_db), current_user = Depends(customer_only)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order or order.order_status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invalid order for payment")
    
    # Create Razorpay order
    receipt_id = f"order_rcptid_{order_id}"
    try:
        razorpay_order = create_razorpay_order(order.total_amount, receipt_id)
        return {
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Razorpay order: {str(e)}")

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    seat_ids: List[int]

@router.post("/orders/{order_id}/verify-razorpay-payment")
def verify_razorpay_payment(order_id: int, payment_data: PaymentVerification, db: Session = Depends(get_db), current_user = Depends(customer_only)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order or order.order_status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invalid order for verification")
    
    # Verify signature
    is_valid = verify_payment_signature(
        payment_data.razorpay_order_id,
        payment_data.razorpay_payment_id,
        payment_data.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    
    # Confirm seats and generate tickets (Logic shared with simulation but adapted)
    seats = db.query(Seat).filter(Seat.id.in_(payment_data.seat_ids), Seat.event_id == order.event_id, Seat.status == "booked").all()
    if len(seats) != len(payment_data.seat_ids):
        raise HTTPException(status_code=400, detail="Seats are no longer available or invalid")

    order.order_status = OrderStatus.CONFIRMED
    order.payment_mode = "razorpay"
    
    # Generate tickets
    tickets = []
    for seat in seats:
        ticket_code = f"TICK-{str(uuid.uuid4()).split('-')[0].upper()}"
        new_ticket = Ticket(
            order_id=order_id,
            seat_id=seat.id,
            ticket_code=ticket_code,
            status=TicketStatus.ACTIVE
        )
        tickets.append(new_ticket)
    
    db.add_all(tickets)
    db.commit()
    
    return {"message": "Payment verified and tickets generated", "order_id": order_id, "ticket_count": len(tickets)}

class PaymentConfirm(BaseModel):
    seat_ids: List[int]

@router.post("/orders/{order_id}/confirm_payment")
def confirm_payment_and_generate_tickets(order_id: int, payment_data: PaymentConfirm, db: Session = Depends(get_db), current_user = Depends(customer_only)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order or order.order_status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invalid order for payment")
    
    # Verify seats are still booked (or 'booked' by this user in this order)
    # The seats were set to 'booked' in place_order.
    seats = db.query(Seat).filter(Seat.id.in_(payment_data.seat_ids), Seat.event_id == order.event_id, Seat.status == "booked").all()
    if len(seats) != len(payment_data.seat_ids):
        raise HTTPException(status_code=400, detail="Seats are no longer available or invalid")

    order.order_status = OrderStatus.CONFIRMED
    
    # Generate tickets
    tickets = []
    for seat in seats:
        # Using cast to string to avoid lint issues with indexing hex
        ticket_code = f"TICK-{str(uuid.uuid4()).split('-')[0].upper()}"
        new_ticket = Ticket(
            order_id=order_id,
            seat_id=seat.id,
            ticket_code=ticket_code,
            status=TicketStatus.ACTIVE
        )
        tickets.append(new_ticket)
    
    db.add_all(tickets)
    db.commit()
    
    return {"message": "Payment successful and tickets generated", "order_id": order_id, "ticket_count": len(tickets)}

@router.get("/tickets")
def view_tickets(db: Session = Depends(get_db), current_user = Depends(customer_only)):
    return db.query(Ticket).join(Order).filter(Order.user_id == current_user.id).all()

@router.post("/refunds")
def request_refund(refund_data: RefundRequestCreate, db: Session = Depends(get_db), current_user = Depends(customer_only)):
    order = db.query(Order).filter(Order.id == refund_data.order_id, Order.user_id == current_user.id).first()
    if not order or order.order_status != OrderStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Invalid order for refund")
    
    event = db.query(Event).filter(Event.id == order.event_id).first()
    if event.event_date < datetime.now():
        raise HTTPException(status_code=400, detail="Refund not allowed after event date")
    
    new_request = RefundRequest(
        order_id=refund_data.order_id,
        requested_by=current_user.id,
        reason=refund_data.reason
    )
    db.add(new_request)
    db.commit()
    return {"message": "Refund request submitted"}

@router.post("/support")
def raise_support_case(case_data: SupportCaseCreate, db: Session = Depends(get_db), current_user = Depends(customer_only)):
    new_case = SupportCase(
        raised_by=current_user.id,
        order_id=case_data.order_id,
        description=case_data.description
    )
    db.add(new_case)
    db.commit()
    return {"message": "Support case raised"}
