from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User, Venue, Event, UserRole, EventStatus
from ..auth import RoleChecker
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = RoleChecker([UserRole.ADMIN])

class VenueCreate(BaseModel):
    name: str
    city: str
    total_capacity: int
    address: str

class EventCreate(BaseModel):
    venue_id: int
    organizer_id: int
    name: str
    category: str
    event_date: datetime
    ticket_price: float
    max_tickets_per_user: int

@router.get("/events/all")
def get_all_events(db: Session = Depends(get_db), current_user = Depends(admin_only)):
    return db.query(Event).all()

@router.get("/venues")
def get_venues(db: Session = Depends(get_db), current_user = Depends(admin_only)):
    return db.query(Venue).all()

@router.get("/organizers")
def get_organizers(db: Session = Depends(get_db), current_user = Depends(admin_only)):
    return db.query(User).filter(User.role == UserRole.ORGANIZER).all()

@router.get("/organizers/{org_id}/profile")
def get_organizer_profile(org_id: int, db: Session = Depends(get_db), current_user = Depends(admin_only)):
    from database.models import OrganizerProfile
    profile = db.query(OrganizerProfile).filter(OrganizerProfile.user_id == org_id).first()
    return profile

@router.post("/seed")
def seed_data(db: Session = Depends(get_db), current_user = Depends(admin_only)):
    # Create Venue if none exists
    venue = db.query(Venue).first()
    if not venue:
        venue = Venue(name="Grand Arena", city="New York", total_capacity=500, address="123 Broadway")
        db.add(venue)
        db.flush()
    
    organizers = db.query(User).filter(User.role == UserRole.ORGANIZER).all()
    if not organizers:
        from ..auth import get_password_hash
        default_org = User(name="Sample Organizer", email="org@example.com", password=get_password_hash("password123"), role=UserRole.ORGANIZER)
        db.add(default_org)
        db.flush()
        organizers = [default_org]
    
    # Create an event for EACH organizer so they all see something
    created_count = 0
    for org in organizers:
        # Check if they already have an event
        existing = db.query(Event).filter(Event.organizer_id == org.id).first()
        if not existing:
            event = Event(
                venue_id=venue.id,
                organizer_id=org.id,
                name=f"Epic Event by {org.name}",
                category="Music",
                event_date=datetime.now(),
                ticket_price=1500.00, # Localized to INR
                max_tickets_per_user=4
            )
            db.add(event)
            created_count += 1
    
    db.commit()
    return {"message": f"Seeded {created_count} events for {len(organizers)} organizers."}

@router.post("/venues")
def add_venue(venue: VenueCreate, db: Session = Depends(get_db), current_user = Depends(admin_only)):
    db_venue = Venue(**venue.dict())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue

@router.post("/events")
def add_event(event: EventCreate, db: Session = Depends(get_db), current_user = Depends(admin_only)):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.patch("/events/{event_id}/status")
def update_event_status(event_id: int, status: EventStatus, db: Session = Depends(get_db), current_user = Depends(admin_only)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db_event.status = status
    db.commit()
    return {"message": f"Event status updated to {status}"}
