import uuid
from datetime import datetime


def new_id() -> str:
    return uuid.uuid4().hex

def date_now() -> datetime:
    return datetime.now()