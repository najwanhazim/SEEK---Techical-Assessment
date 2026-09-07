from typing import List, Optional

from fastapi import APIRouter, Depends

from app.db.store import InMemoryStore, get_store
from app.local_models.jobs import JobIn, JobOut

from app.services import jobs as service

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/create", response_model=JobOut, status_code=201)
def create_job(
        data: JobIn,
        db: InMemoryStore = Depends(get_store)
):
    return service.create_job(db, data=data)

@router.get("/list", response_model=List[JobOut], status_code=200)
def list_jobs(
        status: Optional[bool] = None,
        db: InMemoryStore = Depends(get_store)
):
    return service.list_jobs(db, status=status)

@router.get("/{id}", response_model=JobOut, status_code=200)
def get_job(
        id: str,
        db: InMemoryStore = Depends(get_store)
):
    return service.get_job(db, id=id)

@router.post("/{id}/close", response_model=JobOut, status_code=200)
def close_job(
        id: str,
        db: InMemoryStore = Depends(get_store)
):
    return service.close_job(db, id=id)