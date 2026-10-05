from pymongo import ASCENDING, DESCENDING, MongoClient

from app.core.config import settings


mongo_client = MongoClient(
    settings.MONGODB_URL,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000,
    tz_aware=True,
)
db = mongo_client[settings.DATABASE_NAME]


def ensure_indexes() -> None:
    db.land_applications.create_index("application_id", unique=True)
    db.land_applications.create_index("idempotency_key", unique=True, sparse=True)
    db.land_applications.create_index(
        [("status", ASCENDING), ("timestamps.submitted_at", DESCENDING)]
    )
    db.land_applications.create_index("application_type")
    db.land_applications.create_index("applicant_ref.applicant_id")
    db.land_applications.create_index("parcel_ref.parcel_number")
    db.land_applications.create_index("parcel_ref.zone_id")
    db.land_applications.create_index(
        [
            ("application_id", "text"),
            ("description", "text"),
            ("parcel_ref.parcel_number", "text"),
            ("parcel_ref.block_number", "text"),
        ],
        name="application_search",
    )
    db.parcels.create_index("parcel_id", unique=True)
    db.parcels.create_index("parcel_code", unique=True, sparse=True)
    db.parcels.create_index([("geometry", "2dsphere")], sparse=True)
    db.parcels.create_index("zone_id")
    db.applicants.create_index("identity.national_id", unique=True)
    db.applicants.create_index("contacts.email", unique=True)
    db.staff_members.create_index("staff_code", unique=True)
    db.staff_members.create_index(
        [("role", ASCENDING), ("active", ASCENDING), ("coverage.zone_ids", ASCENDING)]
    )
    db.survey_tasks.create_index("task_id", unique=True)
    db.survey_tasks.create_index("application_id", unique=True)
    db.survey_tasks.create_index("assigned_surveyor_id")
    db.survey_reports.create_index("report_id", unique=True)
    db.survey_reports.create_index("application_id", unique=True)
    db.certificates.create_index("certificate_id", unique=True)
    db.certificates.create_index("application_id", unique=True)
    db.performance_logs.create_index(
        [("application_id", ASCENDING), ("created_at", ASCENDING)]
    )
