from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.user import UserRole
from app.models.test import TestStatus
class TestSchedule(BaseModel):
    scheduled_at: datetime = Field(..., description="When to publish the test")
    application_deadline: Optional[datetime] = None
    assessment_deadline: Optional[datetime] = None
# Base schemas for different operations
class TestBase(BaseModel):
    test_name: str = Field(..., min_length=3, max_length=200, description="Name of the test")
    job_description: str = Field(..., max_length=10000, description="Job description")
    
    @validator('test_name')
    def validate_test_name(cls, v):
        if not v.strip():
            raise ValueError('Test name cannot be empty')
        return v.strip()

class TestCreate(TestBase):
    # Test configuration
    resume_score_threshold: Optional[int] = Field(None, ge=0, le=100)
    max_shortlisted_candidates: Optional[int] = Field(None, ge=1, le=1000)
    auto_shortlist: bool = Field(..., description="Auto shortlist candidates")
    total_questions: Optional[int] = Field(None, ge=1, le=200)
    time_limit_minutes: Optional[int] = Field(None, ge=5, le=480)  # 5 min to 8 hours
    total_marks: Optional[int] = Field(None, ge=1, le=1000)
    high_priority_nodes: Optional[int] = Field(None, description="Count of high priority nodes")
    medium_priority_nodes: Optional[int] = Field(None, description="Count of medium priority nodes")
    low_priority_nodes: Optional[int] = Field(None, description="Count of low priority nodes")
    high_priority_questions: Optional[int] = Field(None, description="Count of high priority questions")
    medium_priority_questions: Optional[int] = Field(None, description="Count of medium priority questions")
    low_priority_questions: Optional[int] = Field(None, description="Count of low priority questions")

class TestUpdate(BaseModel):
    job_description: str = Field(..., max_length=10000, description="Job description")
    resume_score_threshold: Optional[int] = Field(None, ge=0, le=100)
    max_shortlisted_candidates: Optional[int] = Field(None, ge=1, le=1000)
    auto_shortlist: Optional[bool] = None

class TestSchedule(BaseModel):
    scheduled_at: datetime = Field(..., description="When to publish the test")
    application_deadline: Optional[datetime] = None
    assessment_deadline: Optional[datetime] = None

class TestResponse(BaseModel):
    high_priority_questions: Optional[int] = None
    medium_priority_questions: Optional[int] = None
    low_priority_questions: Optional[int] = None
    high_priority_nodes: Optional[int] = None
    medium_priority_nodes: Optional[int] = None
    low_priority_nodes: Optional[int] = None
    test_id: int
    test_name: str
    job_description: Optional[str]
    parsed_job_description: Optional[Dict[str, Any]] = None
    skill_graph: Optional[Dict[str, Any]] = None
    
    # Test configuration
    resume_score_threshold: Optional[int]
    max_shortlisted_candidates: Optional[int]
    auto_shortlist: bool
    total_questions: Optional[int]
    time_limit_minutes: Optional[int]
    total_marks: Optional[int]
    
    # Status and publishing
    status: str
    is_published: bool
    
    # Scheduling
    scheduled_at: Optional[datetime]
    application_deadline: Optional[datetime]
    assessment_deadline: Optional[datetime]
    
    # Audit fields
    created_by: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Creator info (populated by service)
    creator_name: Optional[str] = None
    creator_role: Optional[str] = None
    
    total_candidates: Optional[int] = None
    duration: Optional[int] = None  # in minutes

    class Config:
        from_attributes = True

class TestSummary(BaseModel):
    test_id: int
    test_name: str
    status: str
    is_published: bool
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TestStatusResponse(BaseModel):
    test_id: int
    status: str
    is_published: bool
    scheduled_at: Optional[datetime]
    application_deadline: Optional[datetime]
    assessment_deadline: Optional[datetime]
    
class SkillNode(BaseModel):
    skill: str
    priority: str  # H, M, L
    subskills: List['SkillNode'] = []

class SkillGraph(BaseModel):
    root_nodes: List[SkillNode]

# Enable self-referencing models
SkillNode.model_rebuild()