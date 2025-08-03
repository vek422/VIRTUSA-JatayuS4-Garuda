from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogSchema(BaseModel):
    id: Optional[int]
    timestamp: datetime
    action: str
    status: str
    details: Optional[str]
    user: Optional[str]
    entity: Optional[str]
    source: Optional[str]

    class Config:
        orm_mode = True
