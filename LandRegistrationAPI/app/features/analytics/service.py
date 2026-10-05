from datetime import datetime, timezone

from app.database.mongo import db
from app.shared.serialization import serialize

applications = db["land_applications"]
tasks = db["survey_tasks"]
staff = db["staff_members"]
parcels = db["parcels"]
certificates = db["certificates"]

TERMINAL_STATUSES = ["approved", "certificate_issued", "closed", "rejected"]


def kpis() -> dict:
    total = applications.count_documents({})
    pending = applications.count_documents({"status": {"$nin": TERMINAL_STATUSES}})
    approved = applications.count_documents({"status": {"$in": ["approved", "certificate_issued", "closed"]}})
    rejected = applications.count_documents({"status": "rejected"})
    objections = applications.count_documents({"status": "under_objection"})
    issued = certificates.count_documents({"status": "issued"})
    return {
        "total_applications": total,
        "pending_applications": pending,
        "approved_applications": approved,
        "rejected_applications": rejected,
        "under_objection": objections,
        "certificates_issued": issued,
        "approval_rate": round((approved / total) * 100, 1) if total else 0,
    }


def grouped(field: str, match: dict | None = None, limit: int = 100) -> list[dict]:
    pipeline = []
    if match:
        pipeline.append({"$match": match})
    pipeline.extend(
        [
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": limit},
        ]
    )
    return [{"key": row.get("_id") or "unknown", "count": row["count"]} for row in applications.aggregate(pipeline)]


def processing_time() -> list[dict]:
    pipeline = [
        {"$match": {"timestamps.submitted_at": {"$exists": True}, "timestamps.updated_at": {"$exists": True}}},
        {"$project": {"application_type": 1, "duration": {"$subtract": ["$timestamps.updated_at", "$timestamps.submitted_at"]}}},
        {"$group": {"_id": "$application_type", "average_ms": {"$avg": "$duration"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return [
        {"application_type": row["_id"], "average_hours": round(row["average_ms"] / 3_600_000, 2), "count": row["count"]}
        for row in applications.aggregate(pipeline)
    ]


def surveyors() -> list[dict]:
    rows = staff.find({"role": "surveyor"}, {"name": 1, "staff_code": 1, "workload": 1, "active": 1}).sort("workload.active_tasks", -1)
    return serialize(list(rows))


def registrars() -> list[dict]:
    pipeline = [
        {"$match": {"registrar_review.reviewed_by": {"$exists": True}}},
        {"$group": {"_id": "$registrar_review.reviewed_by", "reviews": {"$sum": 1}, "approved": {"$sum": {"$cond": [{"$eq": ["$registrar_review.decision", "approved"]}, 1, 0]}}}},
        {"$sort": {"reviews": -1}},
    ]
    return [{"registrar": row["_id"], "reviews": row["reviews"], "approved": row["approved"]} for row in applications.aggregate(pipeline)]


def parcel_feed(zone_id: str | None, status: str | None, application_type: str | None, limit: int) -> dict:
    query: dict = {"parcel_ref.geometry": {"$ne": None}}
    if zone_id:
        query["parcel_ref.zone_id"] = zone_id
    if status:
        query["status"] = status
    if application_type:
        query["application_type"] = application_type
    rows = applications.find(query).sort("timestamps.updated_at", -1).limit(limit)
    features = [
        {
            "type": "Feature",
            "geometry": row["parcel_ref"]["geometry"],
            "properties": {
                "application_id": row["application_id"],
                "parcel_id": row["parcel_ref"]["parcel_id"],
                "parcel_number": row["parcel_ref"]["parcel_number"],
                "zone_id": row["parcel_ref"]["zone_id"],
                "status": row["status"],
                "application_type": row["application_type"],
            },
        }
        for row in rows
    ]
    return {"type": "FeatureCollection", "features": serialize(features)}


def pending_heatmap(zone_id: str | None, limit: int) -> dict:
    query: dict = {"status": {"$nin": TERMINAL_STATUSES}, "parcel_ref.geometry.type": "Point"}
    if zone_id:
        query["parcel_ref.zone_id"] = zone_id
    rows = applications.find(query).sort("timestamps.updated_at", -1).limit(limit)
    features = [
        {"type": "Feature", "geometry": row["parcel_ref"]["geometry"], "properties": {"application_id": row["application_id"], "status": row["status"], "weight": 1}}
        for row in rows
    ]
    return {"type": "FeatureCollection", "features": serialize(features)}
