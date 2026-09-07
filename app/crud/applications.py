from typing import List

from app.core.utils import new_id, date_now
from app.db.store import InMemoryStore
from app.db_models.models import Application
from app.local_models.applications import ApplicationIn


def create(db_session: InMemoryStore, *, data: ApplicationIn, job_id: str) -> Application:
    data.id = new_id()
    data.submitted_at = date_now()
    data.job_id = job_id
    data = Application(
        **data.model_dump()
    )
    db_session.applications[data.id] = data
    return data

def get_list_by_job_id(db_session: InMemoryStore, job_id: str) -> List[Application]:
    related_applications = []
    applications = db_session.applications.values()
    for application in applications:
        if application.job_id == job_id:
            related_applications.append(application)
    return related_applications