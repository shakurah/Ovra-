from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional["User"] = None


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[int] = None


# User schemas matching frontend expectations
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None


class UserRegister(BaseModel):
    """Schema for user registration - matches frontend RegisterFormData"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    username: str = Field(..., min_length=3)
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    agree_to_terms: bool = True


class UserLogin(BaseModel):
    """Schema for user login - matches frontend LoginFormData"""
    email: EmailStr
    password: str


class UserCreate(UserBase):
    """Internal schema for creating user"""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user"""
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    """Schema for user response - matches frontend User interface"""
    id: int
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    """Schema for user in database"""
    hashed_password: str


# Rebuild models to resolve forward references
Token.model_rebuild()