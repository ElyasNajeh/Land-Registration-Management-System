from enum import Enum

from bson import ObjectId


def serialize(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value


def page_response(items: list, total: int, page: int, page_size: int) -> dict:
    return {
        "items": serialize(items),
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total else 0,
    }
