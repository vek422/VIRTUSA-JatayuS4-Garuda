"""
Input validation and sanitization utilities
"""
import re
import html
from typing import Optional
from fastapi import HTTPException

class InputValidator:
    """Centralized input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not text:
            return ""
        
        # HTML escape
        sanitized = html.escape(text.strip())
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Basic sanitization
        email = email.strip().lower()
        
        # Email pattern validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check for common email injection patterns
        dangerous_patterns = [
            r'[<>"\']',  # HTML/JS characters
            r'\\',       # Backslashes
            r'/\*',      # Comment starts
            r'\*/',      # Comment ends
            r'--',       # SQL comment
            r';',        # SQL terminator
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, email):
                raise HTTPException(status_code=400, detail="Invalid email format")
        
        return email
    
    @staticmethod
    def validate_password_strength(password: str) -> str:
        """Validate password strength"""
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")
        
        # Check minimum length
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
        # Check maximum length to prevent DoS
        if len(password) > 255:
            raise HTTPException(status_code=400, detail="Password too long")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one digit")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_patterns = [
            r'password',
            r'123456',
            r'qwerty',
            r'admin',
            r'letmein',
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                raise HTTPException(status_code=400, detail="Password is too weak")
        
        return password
    
    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and sanitize name input"""
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        
        # Sanitize
        name = InputValidator.sanitize_string(name, max_length=100)
        
        # Check minimum length
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters long")
        
        # Only allow letters, spaces, hyphens, and periods
        if not re.match(r'^[a-zA-Z\s\-\.]+$', name):
            raise HTTPException(status_code=400, detail="Name can only contain letters, spaces, hyphens, and periods")
        
        return name
