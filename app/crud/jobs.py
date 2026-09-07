import uuid
from datetime import datetime
from typing import List, Optional

from app.core.utils import new_id, date_now
from app.db.store import InMemoryStore
from app.db_models.models import Job
from app.local_models.jobs import JobIn


def create(db_session: InMemoryStore, *, data: JobIn) -> Job:
    data.id = new_id()
    data.created_at = date_now()
    data.status = True
    data = Job(**data.model_dump())
    db_session.jobs[data.id] = data
    return data

def get_list(db_session: InMemoryStore, *, status: Optional[bool]) -> List[Job]:
    jobs = list(db_session.jobs.values())
    if status is not None:
        jobs = [job for job in jobs if job.status is status]
    return jobs

def get_by_id(db_session: InMemoryStore, *, id: str) -> Job:
    print("id: ",id)
    return db_session.jobs.get(id)

def update(db_session: InMemoryStore, *, data: Job) -> Job:
    db_session.jobs[data.id] = data
    return data

def delete(db_session: InMemoryStore, *, id: str) -> None:
    db_session.jobs.pop(id)