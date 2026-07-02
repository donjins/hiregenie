from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from app.config import settings
from app.auth import (
    create_access_token, 
    get_password_hash, 
    verify_password, 
    get_user_by_email
)
from app.database import get_db

router = APIRouter()

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "Recruiter" # Default role

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister):
    db = get_db()
    users_coll = db["users"]
    
    # Check if user already exists
    if get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )
        
    hashed_password = get_password_hash(user_in.password)
    user_record = {
        "name": user_in.name,
        "email": user_in.email,
        "hashed_password": hashed_password,
        "role": user_in.role
    }
    
    res = users_coll.insert_one(user_record)
    user_record["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
    del user_record["hashed_password"]
    
    return {"message": "User registered successfully", "user": user_record}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user.get("role", "Recruiter")},
        expires_delta=access_token_expires
    )
    
    user_data = {
        "id": str(user["_id"]) if "_id" in user else user.get("id"),
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "Recruiter")
    }
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_data}
