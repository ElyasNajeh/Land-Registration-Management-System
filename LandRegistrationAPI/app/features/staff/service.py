from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.database.mongo import db
from app.shared.serialization import page_response, serialize

staff_collection = db["staff_members"]


def _staff_or_404(staff_id: str) -> dict:
    if not ObjectId.is_valid(staff_id):
        raise HTTPException(status_code=400, detail="Invalid staff ID format")
    staff = staff_collection.find_one({"_id": ObjectId(staff_id)})
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


def create_staff(data) -> dict:
    now = datetime.now(timezone.utc)
    document = {**data.model_dump(mode="json"), "created_at": now, "updated_at": now}
    try:
        result = staff_collection.insert_one(document)
    except DuplicateKeyError as error:
        raise HTTPException(status_code=409, detail="Staff code already exists") from error
    document["_id"] = result.inserted_id
    return serialize(document)


def list_staff(search: str | None, role: str | None, active: bool | None, zone_id: str | None, page: int, page_size: int) -> dict:
    query: dict = {}
    if role:
        query["role"] = role
    if active is not None:
        query["active"] = active
    if zone_id:
        query["coverage.zone_ids"] = zone_id
    if search:
        import re

        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [{"staff_code": pattern}, {"name": pattern}, {"contacts.email": pattern}]
    total = staff_collection.count_documents(query)
    rows = list(
        staff_collection.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    )
    return page_response(rows, total, page, page_size)


def get_staff(staff_id: str) -> dict:
    return serialize(_staff_or_404(staff_id))


def update_staff(staff_id: str, data) -> dict:
    staff = _staff_or_404(staff_id)
    updates = data.model_dump(exclude_unset=True, mode="json")
    updates["updated_at"] = datetime.now(timezone.utc)
    result = staff_collection.find_one_and_update(
        {"_id": staff["_id"]}, {"$set": updates}, return_document=ReturnDocument.AFTER
    )
    return serialize(result)
