from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class CandidateApplication(Base):
    __tablename__ = "candidate_applications"

    application_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    test_id = Column(Integer, nullable=False)
    resume_link = Column(String, nullable=False)
    resume_text = Column(Text, nullable=True)
    parsed_resume = Column(Text, nullable=True)
    resume_score = Column(Integer, nullable=True)
    skill_match_percentage = Column(Float, nullable=True)
    experience_score = Column(Integer, nullable=True)
    education_score = Column(Integer, nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    is_shortlisted = Column(Boolean, default=False)
    shortlist_reason = Column(Text, nullable=True)
    screening_completed_at = Column(DateTime, nullable=True)
    screening_status = Column(String(20), default="pending", nullable=False)  # Added for async screening status
    notified_at = Column(DateTime, nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    assessments = relationship(
        "Assessment",
        back_populates="application",
        cascade="all, delete-orphan"
    )
