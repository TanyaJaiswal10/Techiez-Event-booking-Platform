from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User, UserRole, OrganizerProfile
from ..auth import RoleChecker
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/organizer/profile", tags=["organizer-profile"])
organizer_only = RoleChecker([UserRole.ORGANIZER])

class ProfileUpdate(BaseModel):
    company_name: str
    bio: str
    years_of_experience: int
    specialization: str

@router.get("/me")
def get_my_profile(db: Session = Depends(get_db), current_user = Depends(organizer_only)):
    profile = db.query(OrganizerProfile).filter(OrganizerProfile.user_id == current_user.id).first()
    if not profile:
        return {"message": "Profile not created yet"}
    return profile

@router.post("/update")
def update_profile(profile_data: ProfileUpdate, db: Session = Depends(get_db), current_user = Depends(organizer_only)):
    profile = db.query(OrganizerProfile).filter(OrganizerProfile.user_id == current_user.id).first()
    if not profile:
        profile = OrganizerProfile(user_id=current_user.id, **profile_data.dict())
        db.add(profile)
    else:
        for key, value in profile_data.dict().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return {"message": "Profile updated successfully", "profile": profile}
