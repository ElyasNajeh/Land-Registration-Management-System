from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.database.mongo import ensure_indexes, mongo_client
from app.features.analytics.router import router as analytics_router
from app.features.applicants.router import router as applicants_router
from app.features.applications.router import router as applications_router
from app.features.assignments.router import router as assignments_router
from app.features.staff.router import router as staff_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_indexes()
    yield
    mongo_client.close()


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Staff-Key"],
)

for router in (
    applications_router,
    applicants_router,
    staff_router,
    assignments_router,
    analytics_router,
):
    app.include_router(router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["System"])
def health():
    try:
        mongo_client.admin.command("ping")
    except PyMongoError:
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "connected"}
