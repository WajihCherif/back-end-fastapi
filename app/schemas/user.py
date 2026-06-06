from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    RESPONSIBLE = "responsible"

# Base User Schema
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.RESPONSIBLE
    is_active: Optional[bool] = True

# Create User (Request)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

# Update User (Request)
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

# User Response
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Login Schema
class UserLogin(BaseModel):
    username: str
    password: str

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Admin-only create user schema (validates email and allows role assignment)
class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.RESPONSIBLE
    is_active: Optional[bool] = True

class TokenData(BaseModel):
    username: Optional[str] = None