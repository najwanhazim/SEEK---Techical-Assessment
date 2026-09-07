import pytest
from fastapi.testclient import TestClient

from app.core.utils import date_now
from app.crud import applications as applications_crud
from app.crud import jobs as jobs_crud
from app.db.store import InMemoryStore, get_store
from app.local_models.applications import ApplicationIn
from app.local_models.jobs import JobIn
from app.main import app as fastapi_app


@pytest.fixture
def store() -> InMemoryStore:
    """A store scoped to a single test."""
    return InMemoryStore()


@pytest.fixture
def client(store):
    """TestClient backed by the per-test store rather than the singleton."""
    fastapi_app.dependency_overrides[get_store] = lambda: store
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def job_factory(store):
    """Create jobs directly through the CRUD layer, bypassing the service."""

    def _make(
        title="Senior Backend Engineer",
        description="Design and ship Python APIs.",
        location="Kuala Lumpur",
        closed=False,
    ):
        job = jobs_crud.create(
            db_session=store,
            data=JobIn(title=title, description=description, location=location),
        )
        if closed:
            job.status = False
            job.closed_at = date_now()
        return job

    return _make


@pytest.fixture
def open_job(job_factory):
    return job_factory()


@pytest.fixture
def closed_job(job_factory):
    return job_factory(title="Retired Role", closed=True)


@pytest.fixture
def application_factory(store):
    def _make(
        job_id,
        candidate_name="Aisyah Rahman",
        candidate_email="aisyah@example.com",
    ):
        return applications_crud.create(
            store,
            data=ApplicationIn(
                candidate_name=candidate_name,
                candidate_email=candidate_email,
            ),
            job_id=job_id,
        )

    return _make
