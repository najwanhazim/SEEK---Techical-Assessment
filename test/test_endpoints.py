import pytest
from pydantic import ValidationError

VALID_JOB = {
    "title": "Backend Engineer",
    "description": "Build the hiring API.",
    "location": "Kuala Lumpur",
}

VALID_APPLICATION = {
    "candidate_name": "Aisyah Rahman",
    "candidate_email": "aisyah@example.com",
}


class TestCreateJobEndpoint:
    def test_returns_201_with_the_created_job(self, client):
        response = client.post("/jobs/create", json=VALID_JOB)

        assert response.status_code == 201
        body = response.json()
        assert body["id"]
        assert body["title"] == VALID_JOB["title"]
        assert body["description"] == VALID_JOB["description"]
        assert body["location"] == VALID_JOB["location"]
        assert body["status"] is True
        assert body["created_at"] is not None
        assert body["closed_at"] is None

    def test_created_job_is_retrievable(self, client):
        job_id = client.post("/jobs/create", json=VALID_JOB).json()["id"]

        assert client.get(f"/jobs/{job_id}").status_code == 200

    def test_client_supplied_id_and_status_are_overridden(self, client):
        body = client.post(
            "/jobs/create",
            json={**VALID_JOB, "id": "client-chosen-id", "status": False},
        ).json()

        assert body["id"] != "client-chosen-id"
        assert body["status"] is True

    def test_payload_missing_required_fields_is_not_rejected_at_the_boundary(
        self, client
    ):
        with pytest.raises(ValidationError):
            client.post("/jobs/create", json={"location": "Kuala Lumpur"})


class TestListJobsEndpoint:
    def test_returns_empty_list_when_no_jobs_exist(self, client):
        response = client.get("/jobs/list")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_jobs_by_default(self, client, job_factory):
        job_factory(title="Open A")
        job_factory(title="Closed B", closed=True)

        body = client.get("/jobs/list").json()

        assert {job["title"] for job in body} == {"Open A", "Closed B"}

    def test_status_true_returns_only_open_jobs(self, client, job_factory):
        job_factory(title="Open A")
        job_factory(title="Closed B", closed=True)

        body = client.get("/jobs/list", params={"status": True}).json()

        assert [job["title"] for job in body] == ["Open A"]

    def test_status_false_returns_only_closed_jobs(self, client, job_factory):
        job_factory(title="Open A")
        job_factory(title="Closed B", closed=True)

        body = client.get("/jobs/list", params={"status": False}).json()

        assert [job["title"] for job in body] == ["Closed B"]

    def test_non_boolean_status_is_rejected(self, client):
        assert client.get("/jobs/list", params={"status": "maybe"}).status_code == 422

    def test_list_route_is_not_shadowed_by_the_detail_route(self, client, open_job):
        """``/jobs/list`` must keep matching before ``/jobs/{id}``."""
        assert isinstance(client.get("/jobs/list").json(), list)


class TestGetJobEndpoint:
    def test_returns_the_job(self, client, open_job):
        response = client.get(f"/jobs/{open_job.id}")

        assert response.status_code == 200
        assert response.json()["id"] == open_job.id
        assert response.json()["title"] == open_job.title

    def test_returns_404_for_an_unknown_id(self, client):
        response = client.get("/jobs/does-not-exist")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"


class TestCloseJobEndpoint:
    def test_returns_200_with_the_closed_job(self, client, open_job):
        response = client.post(f"/jobs/{open_job.id}/close")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == open_job.id
        assert body["status"] is False
        assert body["closed_at"] is not None

    def test_closure_is_visible_on_subsequent_reads(self, client, open_job):
        client.post(f"/jobs/{open_job.id}/close")

        assert client.get(f"/jobs/{open_job.id}").json()["status"] is False
        assert client.get("/jobs/list", params={"status": True}).json() == []

    def test_closing_twice_is_idempotent(self, client, open_job):
        first = client.post(f"/jobs/{open_job.id}/close").json()
        second = client.post(f"/jobs/{open_job.id}/close")

        assert second.status_code == 200
        assert second.json()["closed_at"] == first["closed_at"]

    def test_returns_404_for_an_unknown_id(self, client):
        response = client.post("/jobs/does-not-exist/close")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"


class TestSubmitApplicationEndpoint:
    def test_returns_201_with_the_created_application(self, client, open_job):
        response = client.post(
            f"/application/{open_job.id}/submit", json=VALID_APPLICATION
        )

        assert response.status_code == 201
        body = response.json()
        assert body["id"]
        assert body["job_id"] == open_job.id
        assert body["candidate_name"] == VALID_APPLICATION["candidate_name"]
        assert body["candidate_email"] == VALID_APPLICATION["candidate_email"]
        assert body["submitted_at"] is not None

    def test_job_id_in_the_payload_is_ignored(self, client, open_job):
        body = client.post(
            f"/application/{open_job.id}/submit",
            json={**VALID_APPLICATION, "job_id": "some-other-job"},
        ).json()

        assert body["job_id"] == open_job.id

    def test_returns_404_when_the_job_does_not_exist(self, client):
        response = client.post(
            "/application/does-not-exist/submit", json=VALID_APPLICATION
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"

    def test_returns_400_when_the_job_is_closed(self, client, closed_job):
        response = client.post(
            f"/application/{closed_job.id}/submit", json=VALID_APPLICATION
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Job is not open for application"

    def test_a_rejected_submission_is_not_stored(self, client, closed_job, store):
        client.post(f"/application/{closed_job.id}/submit", json=VALID_APPLICATION)

        assert store.applications == {}

    def test_payload_missing_candidate_fields_is_not_rejected_at_the_boundary(
        self, client, open_job
    ):
        with pytest.raises(ValidationError):
            client.post(f"/application/{open_job.id}/submit", json={})


class TestListApplicationsEndpoint:
    def test_returns_only_applications_for_the_job(
        self, client, job_factory, application_factory
    ):
        wanted = job_factory(title="Wanted")
        other = job_factory(title="Other")
        mine = application_factory(wanted.id, candidate_email="mine@example.com")
        application_factory(other.id, candidate_email="theirs@example.com")

        response = client.get(f"/application/list/{wanted.id}")

        assert response.status_code == 200
        assert [application["id"] for application in response.json()] == [mine.id]

    def test_returns_empty_list_when_the_job_has_no_applications(self, client, open_job):
        response = client.get(f"/application/list/{open_job.id}")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_404_when_the_job_does_not_exist(self, client):
        response = client.get("/application/list/does-not-exist")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"


class TestJobLifecycle:
    def test_post_job_apply_then_close(self, client):
        job_id = client.post("/jobs/create", json=VALID_JOB).json()["id"]

        submit = client.post(f"/application/{job_id}/submit", json=VALID_APPLICATION)
        assert submit.status_code == 201

        assert len(client.get(f"/application/list/{job_id}").json()) == 1

        assert client.post(f"/jobs/{job_id}/close").status_code == 200

        # Closed jobs stop accepting applications but keep the ones already in.
        rejected = client.post(
            f"/application/{job_id}/submit",
            json={"candidate_name": "Too Late", "candidate_email": "late@example.com"},
        )
        assert rejected.status_code == 400
        assert len(client.get(f"/application/list/{job_id}").json()) == 1
