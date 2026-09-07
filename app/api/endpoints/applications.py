from typing import List

from fastapi import APIRouter, Depends

from app.db.store import InMemoryStore, get_store
from app.db_models.models import Application
from app.local_models.applications import ApplicationOut, ApplicationIn

from app.services import applications as service

router = APIRouter(prefix="/application", tags=["Application"])

@router.post("/{id}/submit", response_model=ApplicationOut, status_code=201)
def submit_application(
        id: str,
        data: ApplicationIn,
        db: InMemoryStore = Depends(get_store),
):
    return service.submit_application(db, job_id=id, data=data)

@router.get("/list/{job_id}", response_model=List[ApplicationOut], status_code=200)
def list_applications(
        job_id: str,
        db: InMemoryStore = Depends(get_store)
):
    return service.list_applications(db, job_id=job_id)