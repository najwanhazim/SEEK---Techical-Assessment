from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobBase(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[bool] = None
    created_at: Optional[datetime] = None

class JobIn(JobBase):
    # id: Optional[str]
    # created_at: Optional[datetime]
    # status: Optional[str]
    # closed_at: Optional[datetime]
    pass

class JobOut(JobBase):
    closed_at: Optional[datetime]