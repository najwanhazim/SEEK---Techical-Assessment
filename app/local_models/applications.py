from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApplicationBase(BaseModel):
    id: Optional[str] = None
    job_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None


class ApplicationIn(ApplicationBase):
    pass

class ApplicationOut(ApplicationBase):
    pass