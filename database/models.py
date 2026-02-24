from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .db import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    CUSTOMER = "customer"
    ENTRY_MANAGER = "entry_manager"
    SUPPORT = "support"

class EventStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class TicketStatus(str, enum.Enum):
    ACTIVE = "active"
    USED = "used"
    CANCELLED = "cancelled"

class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class SupportStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default=UserRole.CUSTOMER)

class OrganizerProfile(Base):
    __tablename__ = "organizer_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    company_name = Column(String)
    bio = Column(String)
    years_of_experience = Column(Integer)
    specialization = Column(String)
    is_verified = Column(Boolean, default=False)
    
    user = relationship("User", backref="profile")

class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    city = Column(String)
    total_capacity = Column(Integer)
    address = Column(String)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"))
    organizer_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    category = Column(String)
    event_date = Column(DateTime)
    ticket_price = Column(Float)
    max_tickets_per_user = Column(Integer)
    status = Column(String, default=EventStatus.UPCOMING)

    venue = relationship("Venue")
    organizer = relationship("User")

class Seat(Base):
    __tablename__ = "seats"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    seat_number = Column(String)
    status = Column(String, default="available") # available, booked

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    total_amount = Column(Float)
    payment_mode = Column(String)
    order_status = Column(String, default=OrderStatus.PENDING)
    booking_time = Column(DateTime, server_default=func.now())

    user = relationship("User")
    event = relationship("Event")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    seat_id = Column(Integer, ForeignKey("seats.id"))
    ticket_code = Column(String, unique=True, index=True)
    status = Column(String, default=TicketStatus.ACTIVE)
    issued_at = Column(DateTime, server_default=func.now())

    order = relationship("Order")
    seat = relationship("Seat")

class RefundRequest(Base):
    __tablename__ = "refund_requests"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    requested_by = Column(Integer, ForeignKey("users.id"))
    reason = Column(String)
    status = Column(String, default=RefundStatus.PENDING)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    requested_at = Column(DateTime, server_default=func.now())

    order = relationship("Order")

class SupportCase(Base):
    __tablename__ = "support_cases"
    id = Column(Integer, primary_key=True, index=True)
    raised_by = Column(Integer, ForeignKey("users.id"))
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    description = Column(String)
    status = Column(String, default=SupportStatus.OPEN)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class EntryLog(Base):
    __tablename__ = "entry_logs"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    validated_by = Column(Integer, ForeignKey("users.id"))
    scanned_at = Column(DateTime, server_default=func.now())
    result = Column(String) # success, failed

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    code = Column(String, unique=True)
    discount_percent = Column(Float)
    valid_until = Column(DateTime)
    max_uses = Column(Integer)
    used_count = Column(Integer, default=0)
