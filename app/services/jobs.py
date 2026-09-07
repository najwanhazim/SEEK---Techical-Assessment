from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException

from app.core.utils import date_now
from app.db.store import InMemoryStore
from app.db_models.models import Job
from app.local_models.jobs import JobIn, JobOut

from app.crud import jobs as crud

def create_job(db_session: InMemoryStore, *, data:JobIn) -> Job:
    return crud.create(db_session=db_session, data=data)

def list_jobs(db_session: InMemoryStore, *, status: Optional[bool]) -> List[Job]:
    jobs = crud.get_list(db_session=db_session, status=status)
    if jobs is None:
        raise HTTPException(status_code=404, detail="List job not found")
    return jobs

def get_job(db_session: InMemoryStore, *, id: str) -> Job:
    job = crud.get_by_id(db_session=db_session, id=id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    return job

def close_job(db_session: InMemoryStore, *, id: str) -> Job:
    job = get_job(db_session=db_session, id=id)
    if not job.status:
        return job
    job.status = False
    job.closed_at = date_now()
    updated_job = crud.update(db_session=db_session, data=job)
    return updated_job
