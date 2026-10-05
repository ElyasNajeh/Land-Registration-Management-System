from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.database.mongo import db
from app.shared.serialization import page_response, serialize
from app.features.applications.services.log_service import create_log

applicants_collection = db["applicants"]
applications_collection = db["land_applications"]
logs_collection = db["performance_logs"]


def _object_id(value: str, label: str = "ID") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label} format")
    return ObjectId(value)


def _applicant_or_404(applicant_id: str) -> dict:
    applicant = applicants_collection.find_one({"_id": _object_id(applicant_id, "applicant ID")})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


def create_applicant(data) -> dict:
    now = datetime.now(timezone.utc)
    document = {
        "full_name": data.full_name.strip(),
        "applicant_type": data.applicant_type.value,
        "identity": {
            "national_id": data.national_id.strip(),
            "verification_state": "unverified",
            "verified_at": None,
        },
        "contacts": data.contacts.model_dump(),
        "address": data.address.model_dump(),
        "preferences": data.preferences.model_dump(),
        "stats": {"total_applications": 0, "approved_applications": 0, "pending_applications": 0},
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = applicants_collection.insert_one(document)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="National ID or email is already registered") from error
    document["_id"] = result.inserted_id
    return serialize(document)


def list_applicants(search: str | None, applicant_type: str | None, page: int, page_size: int) -> dict:
    query: dict = {}
    if applicant_type:
        query["applicant_type"] = applicant_type
    if search:
        import re

        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [{"full_name": pattern}, {"identity.national_id": pattern}, {"contacts.email": pattern}]
    total = applicants_collection.count_documents(query)
    rows = list(
        applicants_collection.find(query, {"identity.national_id": 0})
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return page_response(rows, total, page, page_size)


def get_applicant(applicant_id: str) -> dict:
    applicant = _applicant_or_404(applicant_id)
    applicant.get("identity", {}).pop("national_id", None)
    return serialize(applicant)


def update_applicant(applicant_id: str, data) -> dict:
    applicant = _applicant_or_404(applicant_id)
    updates = data.model_dump(exclude_unset=True)
    if "verification_state" in updates:
        state = updates.pop("verification_state")
        updates["identity.verification_state"] = state
        updates["identity.verified_at"] = datetime.now(timezone.utc) if state == "verified" else None
    updates["updated_at"] = datetime.now(timezone.utc)
    try:
        result = applicants_collection.find_one_and_update(
            {"_id": applicant["_id"]}, {"$set": updates}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="Email is already registered") from error
    return serialize(result)


def list_applicant_applications(applicant_id: str, page: int, page_size: int) -> dict:
    _applicant_or_404(applicant_id)
    query = {"applicant_ref.applicant_id": applicant_id}
    total = applications_collection.count_documents(query)
    rows = list(
        applications_collection.find(query)
        .sort("timestamps.submitted_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return page_response(rows, total, page, page_size)


def add_document(application_id: str, data) -> dict:
    application = applications_collection.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if data.uploaded_by_applicant_id and data.uploaded_by_applicant_id != application["applicant_ref"]["applicant_id"]:
        raise HTTPException(status_code=403, detail="Applicant is not linked to this application")
    now = datetime.now(timezone.utc)
    new_document = {
        "document_id": str(ObjectId()),
        "document_type": data.document_type,
        "required": False,
        "status": "pending_review",
        **data.model_dump(),
        "uploaded_at": now,
    }
    existing = next((doc for doc in application.get("required_documents", []) if doc["document_type"] == data.document_type), None)
    if existing:
        new_document["document_id"] = existing.get("document_id", new_document["document_id"])
        new_document["required"] = existing.get("required", False)
        documents = [new_document if doc.get("document_type") == data.document_type else doc for doc in application.get("required_documents", [])]
        operation = {"$set": {"required_documents": documents, "timestamps.updated_at": now}}
        query = {"_id": application["_id"]}
    else:
        operation = {"$push": {"required_documents": new_document}, "$set": {"timestamps.updated_at": now}}
        query = {"_id": application["_id"]}
    applications_collection.update_one(query, operation)
    create_log(application_id, "document_uploaded", {"document_id": new_document["document_id"], "document_type": data.document_type})
    return serialize(new_document)


def add_comment(application_id: str, data) -> dict:
    application = applications_collection.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    now = datetime.now(timezone.utc)
    note = {"note": data.comment, "visibility": "applicant_visible", "created_at": now}
    applications_collection.update_one(
        {"_id": application["_id"]},
        {"$push": {"internal.notes": note}, "$set": {"timestamps.updated_at": now}},
    )
    create_log(application_id, "applicant_comment_added")
    return serialize(note)


def submit_objection(application_id: str, data) -> dict:
    application = applications_collection.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if application["status"] in {"closed", "rejected", "certificate_issued"}:
        raise HTTPException(status_code=409, detail="An objection cannot be submitted in the current state")
    if data.submitted_by_applicant_id and not ObjectId.is_valid(data.submitted_by_applicant_id):
        raise HTTPException(status_code=400, detail="Invalid applicant ID format")
    now = datetime.now(timezone.utc)
    objection_id = str(ObjectId())
    applications_collection.update_one(
        {"_id": application["_id"]},
        {
            "$set": {
                "status": "under_objection",
                "workflow.current_state": "under_objection",
                "workflow.interrupted_state": application["status"],
                "objection.has_objection": True,
                "timestamps.updated_at": now,
            },
            "$push": {
                "objection.objection_ids": objection_id,
                "objection.items": {"objection_id": objection_id, "reason": data.reason, "submitted_by_applicant_id": data.submitted_by_applicant_id, "submitted_at": now},
            },
        },
    )
    create_log(application_id, "objection_submitted", {"objection_id": objection_id, "reason": data.reason})
    return {"application_id": application_id, "objection_id": objection_id, "status": "under_objection"}


def get_timeline(application_id: str) -> dict:
    application = applications_collection.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    events = list(logs_collection.find({"application_id": application_id}).sort("created_at", 1))
    return {
        "application_id": application_id,
        "current_status": application["status"],
        "total_events": len(events),
        "timeline": [
            {"type": event["action"], "at": event.get("created_at"), "details": event.get("details", {})}
            for event in serialize(events)
        ],
    }
