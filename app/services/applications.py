from typing import List

from fastapi import HTTPException

from app.db.store import InMemoryStore
from app.db_models.models import Application
from app.local_models.applications import ApplicationIn

from app.crud import jobs as jobs_crud
from app.crud import applications as applications_crud


def submit_application(
        db_session: InMemoryStore,
        *,
        job_id: str,
        data: ApplicationIn,
) -> Application:
    job = jobs_crud.get_by_id(db_session, id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.status:
        raise HTTPException(status_code=400, detail="Job is not open for application")

    # application = Application(
    #     job_id=job_id,
    #     **data.model_dump()
    # )

    created_application = applications_crud.create(db_session, data=data, job_id=job_id)

    return created_application

def list_applications(
        db_session: InMemoryStore,
        *,
        job_id: str,
) -> List[Application]:
    job = jobs_crud.get_by_id(db_session, id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    applications = applications_crud.get_list_by_job_id(db_session, job_id=job_id)
    return applications
