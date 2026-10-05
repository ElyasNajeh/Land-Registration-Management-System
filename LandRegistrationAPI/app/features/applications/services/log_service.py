from datetime import datetime, timezone

from app.database.mongo import db

logs_collection = db["performance_logs"]


def create_log(application_id: str, action: str, details: dict | None = None) -> None:
    logs_collection.insert_one(
        {
            "application_id": application_id,
            "action": action,
            "details": details or {},
            "created_at": datetime.now(timezone.utc),
        }
    )
