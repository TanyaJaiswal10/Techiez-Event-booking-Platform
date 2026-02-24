from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Ticket, EntryLog, UserRole, TicketStatus
from ..auth import RoleChecker
from datetime import datetime

router = APIRouter(prefix="/entry", tags=["entry"])
entry_manager_only = RoleChecker([UserRole.ENTRY_MANAGER])

@router.post("/validate/{ticket_code}")
def validate_ticket(ticket_code: str, db: Session = Depends(get_db), current_user = Depends(entry_manager_only)):
    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
    
    result = "failed"
    reason = "Invalid ticket"
    
    if ticket:
        if ticket.status == TicketStatus.ACTIVE:
            result = "success"
            reason = "Valid ticket"
        elif ticket.status == TicketStatus.USED:
            reason = "Ticket already used"
        elif ticket.status == TicketStatus.CANCELLED:
            reason = "Ticket cancelled"
    
    # Log entry attempt
    log = EntryLog(
        ticket_id=ticket.id if ticket else None,
        validated_by=current_user.id,
        result=result
    )
    db.add(log)
    db.commit()
    
    if result == "success":
        return {"message": reason, "ticket_id": ticket.id}
    else:
        raise HTTPException(status_code=400, detail=reason)

@router.patch("/tickets/{ticket_id}/use")
def mark_ticket_as_used(ticket_id: int, db: Session = Depends(get_db), current_user = Depends(entry_manager_only)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket or ticket.status != TicketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Cannot mark as used")
    
    ticket.status = TicketStatus.USED
    db.commit()
    return {"message": "Ticket marked as used"}
