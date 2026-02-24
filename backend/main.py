from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.db import engine, Base, get_db
from database.models import User, UserRole, Order, OrderStatus, Ticket, TicketStatus, Seat
from pydantic import BaseModel
from .auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, RoleChecker, customer_only

from datetime import timedelta
from typing import List, Optional
from .routers import admin, organizer, customer, entry, support, organizer_profile
import uuid

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Ticket Booking Platform API")

app.include_router(admin.router)
app.include_router(organizer.router)
app.include_router(customer.router)
app.include_router(entry.router)
app.include_router(support.router)
app.include_router(organizer_profile.router)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = UserRole.CUSTOMER

@app.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(name=user_data.name, email=user_data.email, password=hashed_pwd, role=user_data.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# Payment and ticket generation are handled in routers/customer.py

