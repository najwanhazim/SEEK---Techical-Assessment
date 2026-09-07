from fastapi import FastAPI

from app.api.endpoints import jobs, applications

app = FastAPI(title="SEEK Technical Assessment", version="1.0")

app.include_router(jobs.router)
app.include_router(applications.router)



