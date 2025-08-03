from sqlalchemy import Column, Integer, String, Enum as SqlEnum, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class UserRole(enum.Enum):
    candidate = "candidate"
    recruiter = "recruiter"

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(SqlEnum(UserRole), nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships - simplified for now
    # created_tests = relationship("Test", foreign_keys="Test.created_by")
    # updated_tests = relationship("Test", foreign_keys="Test.updated_by")