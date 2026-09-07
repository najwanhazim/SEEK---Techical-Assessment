from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Job(BaseModel):
    id: str
    title: str
    description: str
    location: str
    created_at: Optional[datetime]
    status: bool
    closed_at: Optional[datetime] = None

class Application(BaseModel):
    id: str
    job_id: str
    candidate_name: str
    candidate_email: str
    submitted_at: datetime