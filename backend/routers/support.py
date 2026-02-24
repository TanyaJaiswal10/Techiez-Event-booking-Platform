from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import SupportCase, RefundRequest, Order, Seat, Ticket, UserRole, RefundStatus, OrderStatus, TicketStatus
from ..auth import RoleChecker
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/support", tags=["support"])
support_only = RoleChecker([UserRole.SUPPORT])

class ResolutionUpdate(BaseModel):
    status: str
    notes: str

class RefundApproval(BaseModel):
    approve: bool

@router.get("/cases")
def view_support_cases(db: Session = Depends(get_db), current_user = Depends(support_only)):
    return db.query(SupportCase).all()

@router.patch("/cases/{case_id}")
def update_case_status(case_id: int, update: ResolutionUpdate, db: Session = Depends(get_db), current_user = Depends(support_only)):
    case = db.query(SupportCase).filter(SupportCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = update.status
    case.resolution_notes = update.notes
    case.assigned_to = current_user.id
    db.commit()
    return {"message": "Case updated"}

@router.get("/refunds")
def view_refund_requests(db: Session = Depends(get_db), current_user = Depends(support_only)):
    return db.query(RefundRequest).all()

@router.post("/refunds/{refund_id}/approve")
def approve_refund(refund_id: int, approval: RefundApproval, db: Session = Depends(get_db), current_user = Depends(support_only)):
    req = db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Refund request not found")
    
    if approval.approve:
        req.status = RefundStatus.APPROVED
        order = db.query(Order).filter(Order.id == req.order_id).first()
        order.order_status = OrderStatus.REFUNDED
        
        # Free seats and cancel tickets
        tickets = db.query(Ticket).filter(Ticket.order_id == order.id).all()
        for t in tickets:
            t.status = TicketStatus.CANCELLED
            seat = db.query(Seat).filter(Seat.id == t.seat_id).first()
            if seat:
                seat.status = "available"
    else:
        req.status = RefundStatus.REJECTED
    
    req.resolved_by = current_user.id
    req.resolved_at = datetime.now()
    db.commit()
    return {"message": "Refund " + ("approved" if approval.approve else "rejected")}
