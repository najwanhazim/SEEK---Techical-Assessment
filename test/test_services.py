from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.crud import applications as applications_crud
from app.crud import jobs as jobs_crud
from app.local_models.applications import ApplicationIn
from app.local_models.jobs import JobIn
from app.services import applications as applications_service
from app.services import jobs as jobs_service


def assert_recent(value: datetime) -> None:
    assert value is not None
    assert abs(datetime.now() - value) < timedelta(seconds=10)


class TestCreateJob:
    def test_assigns_id_timestamp_and_open_status(self, store):
        job = jobs_service.create_job(
            store,
            data=JobIn(
                title="Backend Engineer",
                description="Build the hiring API.",
                location="Kuala Lumpur",
            ),
        )

        assert job.id
        assert job.title == "Backend Engineer"
        assert job.description == "Build the hiring API."
        assert job.location == "Kuala Lumpur"
        assert job.status is True
        assert job.closed_at is None
        assert_recent(job.created_at)

    def test_persists_job_in_the_store(self, store):
        job = jobs_service.create_job(
            store,
            data=JobIn(title="T", description="D", location="L"),
        )

        assert store.jobs[job.id] is job

    def test_ignores_client_supplied_id_and_status(self, store):
        job = jobs_service.create_job(
            store,
            data=JobIn(
                id="client-chosen-id",
                title="T",
                description="D",
                location="L",
                status=False,
            ),
        )

        assert job.id != "client-chosen-id"
        assert job.status is True

    def test_each_job_gets_a_unique_id(self, store):
        ids = {
            jobs_service.create_job(
                store, data=JobIn(title="T", description="D", location="L")
            ).id
            for _ in range(5)
        }

        assert len(ids) == 5
        assert len(store.jobs) == 5


class TestListJobs:
    def test_returns_empty_list_when_no_jobs_exist(self, store):
        assert jobs_service.list_jobs(store, status=None) == []

    def test_returns_every_job_when_no_status_filter(self, job_factory, store):
        job_factory(title="Open A")
        job_factory(title="Closed B", closed=True)

        titles = {job.title for job in jobs_service.list_jobs(store, status=None)}

        assert titles == {"Open A", "Closed B"}

    def test_filters_to_open_jobs(self, job_factory, store):
        open_a = job_factory(title="Open A")
        job_factory(title="Closed B", closed=True)

        jobs = jobs_service.list_jobs(store, status=True)

        assert [job.id for job in jobs] == [open_a.id]

    def test_filters_to_closed_jobs(self, job_factory, store):
        job_factory(title="Open A")
        closed_b = job_factory(title="Closed B", closed=True)

        jobs = jobs_service.list_jobs(store, status=False)

        assert [job.id for job in jobs] == [closed_b.id]


class TestGetJob:
    def test_returns_the_stored_job(self, store, open_job):
        assert jobs_service.get_job(store, id=open_job.id) is open_job

    def test_raises_404_for_an_unknown_id(self, store):
        with pytest.raises(HTTPException) as exc_info:
            jobs_service.get_job(store, id="does-not-exist")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Job not found"


class TestCloseJob:
    def test_marks_the_job_closed_and_stamps_closed_at(self, store, open_job):
        closed = jobs_service.close_job(store, id=open_job.id)

        assert closed.id == open_job.id
        assert closed.status is False
        assert_recent(closed.closed_at)

    def test_closure_is_persisted(self, store, open_job):
        jobs_service.close_job(store, id=open_job.id)

        assert store.jobs[open_job.id].status is False

    def test_closing_an_already_closed_job_is_idempotent(self, store, open_job):
        first = jobs_service.close_job(store, id=open_job.id)
        original_closed_at = first.closed_at

        second = jobs_service.close_job(store, id=open_job.id)

        assert second.status is False
        assert second.closed_at == original_closed_at

    def test_does_not_touch_other_jobs(self, store, job_factory):
        target = job_factory(title="Target")
        bystander = job_factory(title="Bystander")

        jobs_service.close_job(store, id=target.id)

        assert store.jobs[bystander.id].status is True
        assert store.jobs[bystander.id].closed_at is None

    def test_raises_404_for_an_unknown_id(self, store):
        with pytest.raises(HTTPException) as exc_info:
            jobs_service.close_job(store, id="does-not-exist")

        assert exc_info.value.status_code == 404


class TestSubmitApplication:
    def test_creates_an_application_linked_to_the_job(self, store, open_job):
        application = applications_service.submit_application(
            store,
            job_id=open_job.id,
            data=ApplicationIn(
                candidate_name="Aisyah Rahman",
                candidate_email="aisyah@example.com",
            ),
        )

        assert application.id
        assert application.job_id == open_job.id
        assert application.candidate_name == "Aisyah Rahman"
        assert application.candidate_email == "aisyah@example.com"
        assert_recent(application.submitted_at)
        assert store.applications[application.id] is application

    def test_job_id_comes_from_the_path_not_the_payload(self, store, open_job):
        application = applications_service.submit_application(
            store,
            job_id=open_job.id,
            data=ApplicationIn(
                job_id="some-other-job",
                candidate_name="Aisyah Rahman",
                candidate_email="aisyah@example.com",
            ),
        )

        assert application.job_id == open_job.id

    def test_a_job_accepts_multiple_applications(self, store, open_job):
        for email in ("a@example.com", "b@example.com"):
            applications_service.submit_application(
                store,
                job_id=open_job.id,
                data=ApplicationIn(candidate_name="Candidate", candidate_email=email),
            )

        assert len(store.applications) == 2

    def test_raises_404_when_the_job_does_not_exist(self, store):
        with pytest.raises(HTTPException) as exc_info:
            applications_service.submit_application(
                store,
                job_id="does-not-exist",
                data=ApplicationIn(
                    candidate_name="Aisyah Rahman",
                    candidate_email="aisyah@example.com",
                ),
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Job not found"

    def test_raises_400_when_the_job_is_closed(self, store, closed_job):
        with pytest.raises(HTTPException) as exc_info:
            applications_service.submit_application(
                store,
                job_id=closed_job.id,
                data=ApplicationIn(
                    candidate_name="Aisyah Rahman",
                    candidate_email="aisyah@example.com",
                ),
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Job is not open for application"

    def test_nothing_is_stored_when_a_submission_is_rejected(self, store, closed_job):
        with pytest.raises(HTTPException):
            applications_service.submit_application(
                store,
                job_id=closed_job.id,
                data=ApplicationIn(
                    candidate_name="Aisyah Rahman",
                    candidate_email="aisyah@example.com",
                ),
            )

        assert store.applications == {}


class TestListApplications:
    def test_returns_only_applications_for_the_requested_job(
        self, store, job_factory, application_factory
    ):
        wanted = job_factory(title="Wanted")
        other = job_factory(title="Other")
        mine = application_factory(wanted.id, candidate_email="mine@example.com")
        application_factory(other.id, candidate_email="theirs@example.com")

        applications = applications_service.list_applications(store, job_id=wanted.id)

        assert [application.id for application in applications] == [mine.id]

    def test_returns_empty_list_when_the_job_has_no_applications(self, store, open_job):
        assert applications_service.list_applications(store, job_id=open_job.id) == []

    def test_closed_jobs_still_expose_their_applications(
        self, store, open_job, application_factory
    ):
        application_factory(open_job.id)
        jobs_service.close_job(store, id=open_job.id)

        applications = applications_service.list_applications(store, job_id=open_job.id)

        assert len(applications) == 1

    def test_raises_404_when_the_job_does_not_exist(self, store):
        with pytest.raises(HTTPException) as exc_info:
            applications_service.list_applications(store, job_id="does-not-exist")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Job not found"


class TestCrudLayer:
    def test_get_by_id_returns_none_rather_than_raising(self, store):
        assert jobs_crud.get_by_id(db_session=store, id="does-not-exist") is None

    def test_update_replaces_the_stored_job(self, store, open_job):
        open_job.title = "Renamed"

        updated = jobs_crud.update(db_session=store, data=open_job)

        assert updated.title == "Renamed"
        assert store.jobs[open_job.id].title == "Renamed"

    def test_delete_removes_the_job(self, store, open_job):
        jobs_crud.delete(db_session=store, id=open_job.id)

        assert open_job.id not in store.jobs

    def test_get_list_by_job_id_matches_on_job_id(
        self, store, job_factory, application_factory
    ):
        job = job_factory()
        application_factory(job.id)

        assert applications_crud.get_list_by_job_id(store, job_id=job.id) != []
        assert applications_crud.get_list_by_job_id(store, job_id="other") == []
