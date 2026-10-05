from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.database.mongo import db
from app.shared.serialization import page_response, serialize
from ..enums import ApplicationStatus
from .log_service import create_log
from .workflow_service import allowed_next, validate_transition

applications_collection = db["land_applications"]
applicants_collection = db["applicants"]
parcels_collection = db["parcels"]
certificates_collection = db["certificates"]
counters_collection = db["counters"]

REQUIRED_DOCUMENTS = {
    "first_registration": ["ownership_deed", "id_copy"],
    "ownership_transfer": ["ownership_deed", "id_copy", "sale_contract"],
    "parcel_subdivision": ["ownership_deed", "id_copy"],
    "parcel_merge": ["ownership_deed", "id_copy"],
    "boundary_correction": ["ownership_deed", "id_copy"],
    "certificate_request": ["id_copy", "ownership_deed"],
}


def _application_or_404(application_id: str) -> dict:
    application = applications_collection.find_one({"application_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def _next_id(prefix: str, counter_key: str) -> str:
    year = datetime.now(timezone.utc).year
    result = counters_collection.find_one_and_update(
        {"_id": f"{counter_key}-{year}"},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"{prefix}-{year}-{result['sequence']:04d}"


def _documents(application_type: str, submitted: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc)
    provided = {doc["document_type"]: doc for doc in submitted}
    document_types = list(dict.fromkeys(REQUIRED_DOCUMENTS.get(application_type, []) + list(provided)))
    return [
        {
            "document_id": str(ObjectId()),
            "document_type": document_type,
            "required": document_type in REQUIRED_DOCUMENTS.get(application_type, []),
            "status": "pending_review" if provided.get(document_type, {}).get("file_name") else "missing",
            **provided.get(document_type, {}),
            "uploaded_at": now if provided.get(document_type, {}).get("file_name") else None,
        }
        for document_type in document_types
    ]


def create_application(data, idempotency_key: str | None = None) -> dict:
    if idempotency_key:
        existing = applications_collection.find_one({"idempotency_key": idempotency_key})
        if existing:
            return serialize(existing)

    if not ObjectId.is_valid(data.applicant_id) or not applicants_collection.find_one({"_id": ObjectId(data.applicant_id)}):
        raise HTTPException(status_code=422, detail="A valid existing applicant_id is required")

    now = datetime.now(timezone.utc)
    parcel = {
        "parcel_id": data.parcel_id.strip(),
        "parcel_number": data.parcel_number.strip(),
        "block_number": data.block_number.strip(),
        "basin_number": data.basin_number.strip(),
        "zone_id": data.zone_id.strip(),
        "geometry": data.geometry.model_dump() if data.geometry else None,
    }
    application_type = data.application_type.value
    application_id = _next_id("LRMIS", "application")
    application = {
        "application_id": application_id,
        "idempotency_key": idempotency_key,
        "application_type": application_type,
        "status": ApplicationStatus.SUBMITTED.value,
        "priority": data.priority,
        "description": data.description,
        "tags": [application_type],
        "applicant_ref": {"applicant_id": data.applicant_id},
        "parcel_ref": parcel,
        "workflow": {
            "current_state": ApplicationStatus.SUBMITTED.value,
            "allowed_next": [ApplicationStatus.PRE_CHECKED.value],
            "transition_rules_version": "1.0",
        },
        "required_documents": _documents(application_type, [doc.model_dump() for doc in data.documents]),
        "timestamps": {"submitted_at": now, "updated_at": now},
        "assignment": {"assigned_surveyor_id": None, "assigned_registrar_id": None},
        "objection": {"has_objection": False, "objection_ids": []},
        "internal": {"notes": []},
    }
    try:
        applications_collection.insert_one(application)
    except DuplicateKeyError:
        if idempotency_key:
            return serialize(applications_collection.find_one({"idempotency_key": idempotency_key}))
        raise HTTPException(status_code=409, detail="Application already exists")

    parcels_collection.update_one(
        {"parcel_id": data.parcel_id},
        {"$set": {**parcel, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    applicants_collection.update_one(
        {"_id": ObjectId(data.applicant_id)},
        {"$inc": {"stats.total_applications": 1, "stats.pending_applications": 1}},
    )
    create_log(application_id, "application_created", {"status": "submitted"})
    return serialize(application)


def get_application(application_id: str) -> dict:
    application = _application_or_404(application_id)
    application["workflow"]["allowed_next"] = allowed_next(application)
    return serialize(application)


def list_applications(filters: dict, page: int, page_size: int, sort_field: str, sort_order: int) -> dict:
    query: dict = {}
    for key in ("status", "application_type", "priority"):
        if filters.get(key):
            query[key] = filters[key]
    mappings = {
        "zone_id": "parcel_ref.zone_id",
        "applicant_id": "applicant_ref.applicant_id",
        "parcel_number": "parcel_ref.parcel_number",
    }
    for source, target in mappings.items():
        if filters.get(source):
            query[target] = filters[source]
    if filters.get("search"):
        escaped = __import__("re").escape(filters["search"].strip())
        query["$or"] = [
            {"application_id": {"$regex": escaped, "$options": "i"}},
            {"description": {"$regex": escaped, "$options": "i"}},
            {"parcel_ref.parcel_number": {"$regex": escaped, "$options": "i"}},
        ]
    if filters.get("date_from") or filters.get("date_to"):
        query["timestamps.submitted_at"] = {}
        if filters.get("date_from"):
            query["timestamps.submitted_at"]["$gte"] = filters["date_from"]
        if filters.get("date_to"):
            query["timestamps.submitted_at"]["$lte"] = filters["date_to"]

    total = applications_collection.count_documents(query)
    items = list(
        applications_collection.find(query)
        .sort(sort_field, sort_order)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return page_response(items, total, page, page_size)


def update_application(application_id: str, data) -> dict:
    application = _application_or_404(application_id)
    if application["status"] not in {"submitted", "missing_documents", "on_hold"}:
        raise HTTPException(status_code=409, detail="Only pending applications can be edited")
    updates = {key: value for key, value in data.model_dump(exclude_unset=True).items()}
    if not updates:
        return serialize(application)
    updates["timestamps.updated_at"] = datetime.now(timezone.utc)
    result = applications_collection.find_one_and_update(
        {"application_id": application_id}, {"$set": updates}, return_document=ReturnDocument.AFTER
    )
    create_log(application_id, "application_updated", {"fields": list(updates)})
    return serialize(result)


def delete_application(application_id: str) -> dict:
    application = _application_or_404(application_id)
    if application["status"] != "submitted":
        raise HTTPException(status_code=409, detail="Only submitted applications can be deleted")
    applications_collection.delete_one({"_id": application["_id"]})
    applicants_collection.update_one(
        {"_id": ObjectId(application["applicant_ref"]["applicant_id"])},
        {"$inc": {"stats.total_applications": -1, "stats.pending_applications": -1}},
    )
    create_log(application_id, "application_deleted")
    return {"message": "Application deleted"}


def transition_application(application_id: str, new_status) -> dict:
    application = _application_or_404(application_id)
    validate_transition(application, new_status)
    target = new_status.value
    now = datetime.now(timezone.utc)
    updates = {
        "status": target,
        "workflow.current_state": target,
        "workflow.allowed_next": ALLOWED_TRANSITIONS_VALUES.get(target, []),
        "timestamps.updated_at": now,
        f"timestamps.{target}_at": now,
    }
    result = applications_collection.find_one_and_update(
        {"_id": application["_id"], "status": application["status"]},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(status_code=409, detail="Application changed; reload and try again")
    create_log(application_id, "status_changed", {"from": application["status"], "to": target})
    return serialize(result)


ALLOWED_TRANSITIONS_VALUES = {
    "submitted": ["pre_checked"], "pre_checked": ["survey_required", "legal_review"],
    "survey_required": ["surveyed"], "surveyed": ["legal_review"],
    "legal_review": ["approved"], "approved": [],
    "certificate_issued": ["closed"],
}


def interrupt_application(application_id: str, target: str, reason: str, field: str) -> dict:
    application = _application_or_404(application_id)
    if application["status"] in {"closed", "certificate_issued", "rejected"}:
        raise HTTPException(status_code=409, detail="This application can no longer be interrupted")
    now = datetime.now(timezone.utc)
    updates = {
        "status": target,
        "workflow.current_state": target,
        "workflow.interrupted_state": application["status"],
        field: reason,
        "timestamps.updated_at": now,
    }
    result = applications_collection.find_one_and_update(
        {"_id": application["_id"]}, {"$set": updates}, return_document=ReturnDocument.AFTER
    )
    create_log(application_id, f"application_{target}", {"reason": reason})
    return serialize(result)


def mark_missing_documents(application_id: str, documents: list[str]) -> dict:
    application = _application_or_404(application_id)
    existing = {doc["document_type"]: doc for doc in application.get("required_documents", [])}
    for document_type in documents:
        existing.setdefault(document_type, {"document_id": str(ObjectId()), "document_type": document_type})
        existing[document_type].update({"required": True, "status": "missing"})
    result = interrupt_application(application_id, "missing_documents", ", ".join(documents), "missing_documents_reason")
    applications_collection.update_one(
        {"application_id": application_id}, {"$set": {"required_documents": list(existing.values())}}
    )
    result["required_documents"] = list(existing.values())
    return serialize(result)


def reject_application(application_id: str, reason: str) -> dict:
    application = _application_or_404(application_id)
    if application["status"] in {"closed", "certificate_issued", "rejected"}:
        raise HTTPException(status_code=409, detail="Application cannot be rejected")
    now = datetime.now(timezone.utc)
    result = applications_collection.find_one_and_update(
        {"_id": application["_id"]},
        {"$set": {"status": "rejected", "workflow.current_state": "rejected", "rejection_reason": reason, "timestamps.rejected_at": now, "timestamps.updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    applicant_id = application.get("applicant_ref", {}).get("applicant_id")
    if ObjectId.is_valid(applicant_id):
        applicants_collection.update_one(
            {"_id": ObjectId(applicant_id), "stats.pending_applications": {"$gt": 0}},
            {"$inc": {"stats.pending_applications": -1}},
        )
    create_log(application_id, "application_rejected", {"reason": reason})
    return serialize(result)


def add_note(application_id: str, note: str, visibility: str) -> dict:
    _application_or_404(application_id)
    item = {"note": note, "visibility": visibility, "created_at": datetime.now(timezone.utc)}
    result = applications_collection.find_one_and_update(
        {"application_id": application_id},
        {"$push": {"internal.notes": item}, "$set": {"timestamps.updated_at": item["created_at"]}},
        return_document=ReturnDocument.AFTER,
    )
    create_log(application_id, "note_added", {"visibility": visibility})
    return serialize(result)


def review_document(application_id: str, document_id: str, data) -> dict:
    application = _application_or_404(application_id)
    now = datetime.now(timezone.utc)
    found = False
    documents = application.get("required_documents", [])
    for document in documents:
        if document.get("document_id") == document_id:
            document.update(
                {
                    "status": data.status,
                    "review_notes": data.notes,
                    "reviewed_at": now,
                }
            )
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Document not found")
    result = applications_collection.find_one_and_update(
        {"_id": application["_id"]},
        {"$set": {"required_documents": documents, "timestamps.updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    create_log(application_id, "document_reviewed", {"document_id": document_id, "status": data.status})
    return serialize(result)


def generate_certificate(application_id: str) -> dict:
    application = _application_or_404(application_id)
    existing = certificates_collection.find_one({"application_id": application_id})
    if existing:
        return serialize(existing)
    if application["status"] != "approved":
        raise HTTPException(status_code=409, detail="Application must be approved before certificate issuance")
    now = datetime.now(timezone.utc)
    certificate = {
        "certificate_id": _next_id("CERT", "certificate"),
        "application_id": application_id,
        "parcel_id": application["parcel_ref"]["parcel_id"],
        "issued_to": {"applicant_id": application["applicant_ref"]["applicant_id"]},
        "status": "issued",
        "issued_at": now,
        "verification": {"qr_code_url": f"/certificates/{application_id}/verify", "digital_signature_stub": uuid4().hex},
    }
    certificates_collection.insert_one(certificate)
    applications_collection.update_one(
        {"_id": application["_id"]},
        {"$set": {"status": "certificate_issued", "workflow.current_state": "certificate_issued", "certificate_id": certificate["certificate_id"], "timestamps.certificate_issued_at": now, "timestamps.updated_at": now}},
    )
    create_log(application_id, "certificate_issued", {"certificate_id": certificate["certificate_id"]})
    return serialize(certificate)
