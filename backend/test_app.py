#!/usr/bin/env python3

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn

# Simple in-memory storage for testing
users_db = {}
user_id_counter = 1

# Test schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User

# Create FastAPI app
app = FastAPI(title="OVRA AI Backend", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "OVRA AI Backend is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/auth/register", response_model=User)
async def register(user_data: UserRegister):
    global user_id_counter
    
    # Check if user exists
    for user in users_db.values():
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if user["username"] == user_data.username:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    new_user = {
        "id": user_id_counter,
        "email": user_data.email,
        "username": user_data.username,
        "password": user_data.password,  # In real app, this would be hashed
        "full_name": user_data.full_name,
        "company": user_data.company,
        "phone": user_data.phone,
        "is_active": True
    }
    
    users_db[user_id_counter] = new_user
    user_id_counter += 1
    
    # Return user without password
    return User(**{k: v for k, v in new_user.items() if k != "password"})

@app.post("/api/v1/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user = None
    for u in users_db.values():
        if u["email"] == user_data.email and u["password"] == user_data.password:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create mock tokens
    access_token = f"mock_access_token_for_user_{user['id']}"
    refresh_token = f"mock_refresh_token_for_user_{user['id']}"
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=User(**{k: v for k, v in user.items() if k != "password"})
    )

@app.get("/api/v1/auth/me", response_model=User)
async def get_current_user():
    # Mock current user for testing
    if users_db:
        first_user = next(iter(users_db.values()))
        return User(**{k: v for k, v in first_user.items() if k != "password"})
    else:
        raise HTTPException(status_code=401, detail="No users found")

if __name__ == "__main__":
    print("🚀 Starting OVRA AI Backend...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000/api/v1")
    
    uvicorn.run(
        "test_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )