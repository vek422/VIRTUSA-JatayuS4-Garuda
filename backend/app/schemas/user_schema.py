from datetime import date, datetime
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from app.models.user import UserRole
import re

class UserPublic(BaseModel):
    user_id: int
    name: str
    email: str
    role: UserRole
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=255)
    
    @validator('email')
    def validate_email(cls, v):
        # Additional email sanitization
        return v.lower().strip()
    
    @validator('password')
    def validate_password(cls, v):
        # Sanitize password input
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v.strip()

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    role: UserRole
    
    @validator('name')
    def validate_name(cls, v):
        # Sanitize name input
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        # Remove extra spaces and limit to alphanumeric + basic punctuation
        sanitized = re.sub(r'[^\w\s\-\.]', '', v.strip())
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Replace multiple spaces with single
        if len(sanitized) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return sanitized
    
    @validator('email')
    def validate_email(cls, v):
        # Additional email sanitization
        return v.lower().strip()
    
    @validator('password')
    def validate_password(cls, v):
        # Password strength validation
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        
        password = v.strip()
        
        # Check minimum length
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('Password must contain at least one special character')
        
        return password

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: UserRole
    
    class Config:
        from_attributes = True
