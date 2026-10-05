from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReturnDocument

from app.database.mongo import db
from app.shared.serialization import page_response, serialize
from app.features.applications.services.log_service import create_log

applications = db["land_applications"]
staff = db["staff_members"]
tasks = db["survey_tasks"]
reports = db["survey_reports"]
applicants = db["applicants"]

MILESTONE_SEQUENCE = {
    "assigned": "visit_scheduled",
    "visit_scheduled": "arrived_on_site",
    "arrived_on_site": "survey_started",
    "survey_started": "survey_completed",
}


def _application_or_404(application_id: str) -> dict:
    application = applications.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def _task_or_404(application_id: str) -> dict:
    task = tasks.find_one({"application_id": application_id})
    if not task:
        raise HTTPException(status_code=404, detail="Survey task not found")
    return task


def list_tasks(
    surveyor_id: str | None, task_status: str | None, zone_id: str | None, page: int, page_size: int
) -> dict:
    query: dict = {}
    if surveyor_id:
        if not ObjectId.is_valid(surveyor_id):
            raise HTTPException(status_code=400, detail="Invalid surveyor ID")
        query["assigned_surveyor_id"] = ObjectId(surveyor_id)
    if task_status:
        query["status"] = task_status
    if zone_id:
        query["zone_id"] = zone_id
    total = tasks.count_documents(query)
    rows = list(tasks.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size))
    return page_response(rows, total, page, page_size)


def auto_assign_surveyor(application_id: str) -> dict:
    application = _application_or_404(application_id)
    if application["status"] != "survey_required":
        raise HTTPException(status_code=409, detail="Application must be in survey_required state")
    existing = tasks.find_one({"application_id": application_id})
    if existing:
        return serialize(existing)
    zone = application.get("parcel_ref", {}).get("zone_id")
    if not zone:
        raise HTTPException(status_code=409, detail="Application parcel zone is missing")

    candidates = list(staff.find({"role": "surveyor", "active": True, "coverage.zone_ids": zone}).limit(200))
    candidates = [
        member
        for member in candidates
        if member.get("workload", {}).get("active_tasks", 0) < member.get("workload", {}).get("max_tasks", 0)
    ]
    if not candidates:
        raise HTTPException(status_code=404, detail="No available surveyor covers this zone")
    application_type = application.get("application_type")
    candidates.sort(
        key=lambda member: (
            0 if application_type in member.get("skills", []) else 1,
            member.get("workload", {}).get("active_tasks", 0) / max(member.get("workload", {}).get("max_tasks", 1), 1),
            member.get("staff_code", ""),
        )
    )
    surveyor = candidates[0]
    now = datetime.now(timezone.utc)
    task = {
        "task_id": f"SURV-{now.year}-{uuid4().hex[:8].upper()}",
        "application_id": application_id,
        "parcel_id": application["parcel_ref"]["parcel_id"],
        "zone_id": zone,
        "priority": application.get("priority", "normal"),
        "assigned_surveyor_id": surveyor["_id"],
        "assigned_surveyor_name": surveyor["name"],
        "status": "assigned",
        "milestones": [{"type": "assigned", "at": now, "by": "system", "meta": {"reason": "zone, skill, capacity, and workload match"}}],
        "field_notes": [],
        "report_uploaded": False,
        "created_at": now,
        "updated_at": now,
    }
    tasks.insert_one(task)
    staff.update_one({"_id": surveyor["_id"]}, {"$inc": {"workload.active_tasks": 1}})
    applications.update_one(
        {"_id": application["_id"]},
        {"$set": {"assignment.assigned_surveyor_id": surveyor["_id"], "assignment.assignment_policy": "zone+skill+capacity+workload", "timestamps.updated_at": now}},
    )
    create_log(application_id, "survey_assigned", {"task_id": task["task_id"], "surveyor_id": str(surveyor["_id"])})
    return serialize(task)


def add_milestone(application_id: str, data) -> dict:
    _application_or_404(application_id)
    task = _task_or_404(application_id)
    expected = MILESTONE_SEQUENCE.get(task["status"])
    target = data.milestone_type.value
    if target != expected:
        raise HTTPException(status_code=409, detail=f"Next milestone must be {expected or 'none'}")
    now = datetime.now(timezone.utc)
    milestone = {"type": target, "at": now, "by": data.by.value, "meta": data.meta}
    result = tasks.find_one_and_update(
        {"_id": task["_id"], "status": task["status"]},
        {"$push": {"milestones": milestone}, "$set": {"status": target, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=409, detail="Task changed; reload and try again")
    create_log(application_id, "survey_milestone_added", {"task_id": task["task_id"], "milestone": target})
    return serialize(result)


def add_report(application_id: str, data) -> dict:
    application = _application_or_404(application_id)
    task = _task_or_404(application_id)
    if task["status"] != "survey_completed":
        raise HTTPException(status_code=409, detail="Survey must be completed before report upload")
    existing = reports.find_one({"application_id": application_id})
    if existing:
        return serialize(existing)
    now = datetime.now(timezone.utc)
    report = {
        "report_id": f"REP-{now.year}-{uuid4().hex[:8].upper()}",
        "application_id": application_id,
        "task_id": task["task_id"],
        **data.model_dump(),
        "created_at": now,
    }
    reports.insert_one(report)
    tasks.update_one(
        {"_id": task["_id"]},
        {"$push": {"milestones": {"type": "report_uploaded", "at": now, "by": "surveyor", "meta": {"report_id": report["report_id"]}}}, "$set": {"status": "report_uploaded", "report_uploaded": True, "updated_at": now}},
    )
    applications.update_one(
        {"_id": application["_id"]},
        {"$set": {"status": "surveyed", "workflow.current_state": "surveyed", "workflow.allowed_next": ["legal_review"], "survey.report_id": report["report_id"], "timestamps.surveyed_at": now, "timestamps.updated_at": now}},
    )
    create_log(application_id, "survey_report_uploaded", {"report_id": report["report_id"]})
    return serialize(report)


def registrar_review(application_id: str, data) -> dict:
    application = _application_or_404(application_id)
    task = _task_or_404(application_id)
    report = reports.find_one({"application_id": application_id})
    if not report or task["status"] != "report_uploaded":
        raise HTTPException(status_code=409, detail="A survey report is required before registrar review")
    if application["status"] not in {"surveyed", "legal_review"}:
        raise HTTPException(status_code=409, detail="Application is not ready for registrar review")
    if data.decision.value == "approved":
        unverified = [doc["document_type"] for doc in application.get("required_documents", []) if doc.get("required") and doc.get("status") != "verified"]
        if unverified:
            raise HTTPException(status_code=409, detail=f"Documents require verification: {', '.join(unverified)}")
        new_status = "approved"
    elif data.decision.value == "rejected":
        new_status = "rejected"
    else:
        new_status = "on_hold"
    now = datetime.now(timezone.utc)
    review = {"reviewed_by": data.reviewed_by, "decision": data.decision.value, "notes": data.notes, "reviewed_at": now}
    applications.update_one(
        {"_id": application["_id"]},
        {"$set": {"status": new_status, "workflow.current_state": new_status, "workflow.allowed_next": ["certificate_issued"] if new_status == "approved" else [], "registrar_review": review, "timestamps.legal_review_at": now, f"timestamps.{new_status}_at": now, "timestamps.updated_at": now}},
    )
    tasks.update_one(
        {"_id": task["_id"]},
        {"$push": {"milestones": {"type": "registrar_reviewed", "at": now, "by": "registrar", "meta": review}}, "$set": {"status": "registrar_reviewed", "updated_at": now}},
    )
    staff.update_one({"_id": task["assigned_surveyor_id"], "workload.active_tasks": {"$gt": 0}}, {"$inc": {"workload.active_tasks": -1}})
    if ObjectId.is_valid(application["applicant_ref"]["applicant_id"]):
        increments = {"stats.pending_applications": -1}
        if new_status == "approved":
            increments["stats.approved_applications"] = 1
        applicants.update_one({"_id": ObjectId(application["applicant_ref"]["applicant_id"])}, {"$inc": increments})
    create_log(application_id, "registrar_reviewed", {"decision": data.decision.value, "status": new_status})
    return {"application_id": application_id, "task_id": task["task_id"], "report_id": report["report_id"], "decision": data.decision.value, "status": new_status}
