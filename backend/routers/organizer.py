from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Event, Seat, UserRole, Order, EventStatus, Venue
from ..auth import RoleChecker
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/organizer", tags=["organizer"])
organizer_only = RoleChecker([UserRole.ORGANIZER])

@router.get("/events/me")
def get_my_events(db: Session = Depends(get_db), current_user = Depends(organizer_only)):
    return db.query(Event).filter(Event.organizer_id == current_user.id).all()

@router.post("/events/{event_id}/seats")
def create_seats(event_id: int, seat_count: int, db: Session = Depends(get_db), current_user = Depends(organizer_only)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this event")
    
    venue = db.query(Venue).filter(Venue.id == event.venue_id).first()
    if not venue:
         raise HTTPException(status_code=404, detail="Venue not found")

    existing_seats_count = db.query(Seat).filter(Seat.event_id == event_id).count()
    
    if existing_seats_count + seat_count > venue.total_capacity:
        raise HTTPException(status_code=400, detail=f"Total seats exceed venue capacity of {venue.total_capacity}")

    new_seats = []
    for i in range(seat_count):
        seat_num = f"S{existing_seats_count + i + 1}"
        new_seats.append(Seat(event_id=event_id, seat_number=seat_num, status="available"))
    
    db.add_all(new_seats)
    db.commit()
    return {"message": f"{seat_count} additional seats created for event {event_id}. Total now: {existing_seats_count + seat_count}"}

@router.get("/events/{event_id}/summary")
def view_booking_summary(event_id: int, db: Session = Depends(get_db), current_user = Depends(organizer_only)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this event's summary")
    
    booked_count = db.query(Seat).filter(Seat.event_id == event_id, Seat.status == "booked").count()
    total_seats = db.query(Seat).filter(Seat.event_id == event_id).count()
    
    from sqlalchemy import func
    revenue = db.query(func.sum(Order.total_amount)).filter(Order.event_id == event_id, Order.order_status == "confirmed").scalar() or 0
    
    return {
        "event_name": event.name,
        "total_seats": total_seats,
        "booked_seats": booked_count,
        "revenue": revenue
    }

@router.patch("/events/{event_id}/close")
def close_bookings(event_id: int, db: Session = Depends(get_db), current_user = Depends(organizer_only)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = EventStatus.CLOSED
    db.commit()
    return {"message": "Bookings closed"}
