from typing import Dict

from app.db_models.models import Job, Application


class InMemoryStore:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.applications: Dict[str, Application] = {}

store = InMemoryStore()

def get_store() -> InMemoryStore:
    return store