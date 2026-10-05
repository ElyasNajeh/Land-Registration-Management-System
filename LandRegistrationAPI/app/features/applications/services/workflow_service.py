from fastapi import HTTPException, status

from ..enums import ApplicationStatus


ALLOWED_TRANSITIONS = {
    ApplicationStatus.SUBMITTED.value: [ApplicationStatus.PRE_CHECKED.value],
    ApplicationStatus.PRE_CHECKED.value: [
        ApplicationStatus.SURVEY_REQUIRED.value,
        ApplicationStatus.LEGAL_REVIEW.value,
    ],
    ApplicationStatus.SURVEY_REQUIRED.value: [ApplicationStatus.SURVEYED.value],
    ApplicationStatus.SURVEYED.value: [ApplicationStatus.LEGAL_REVIEW.value],
    ApplicationStatus.LEGAL_REVIEW.value: [ApplicationStatus.APPROVED.value],
    ApplicationStatus.APPROVED.value: [],
    ApplicationStatus.CERTIFICATE_ISSUED.value: [ApplicationStatus.CLOSED.value],
}


def allowed_next(application: dict) -> list[str]:
    status_value = str(application.get("status"))
    if status_value in {
        ApplicationStatus.ON_HOLD.value,
        ApplicationStatus.MISSING_DOCUMENTS.value,
        ApplicationStatus.UNDER_OBJECTION.value,
    }:
        previous = application.get("workflow", {}).get("interrupted_state")
        return [previous] if previous else []
    return ALLOWED_TRANSITIONS.get(status_value, [])


def validate_transition(application: dict, new_status: ApplicationStatus) -> None:
    target = new_status.value
    if target not in allowed_next(application):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from {application.get('status')} to {target}",
        )

    parcel = application.get("parcel_ref", {})
    documents = application.get("required_documents", [])
    if target == ApplicationStatus.PRE_CHECKED.value:
        required = ["applicant_id"]
        if any(not application.get("applicant_ref", {}).get(field) for field in required):
            raise HTTPException(status_code=409, detail="Applicant information is incomplete")
        parcel_fields = ("parcel_id", "parcel_number", "block_number", "basin_number", "zone_id")
        if any(not parcel.get(field) for field in parcel_fields):
            raise HTTPException(status_code=409, detail="Parcel information is incomplete")
        missing = [doc["document_type"] for doc in documents if doc.get("required") and not doc.get("file_name")]
        if missing:
            raise HTTPException(status_code=409, detail=f"Required documents are missing: {', '.join(missing)}")
    elif target == ApplicationStatus.SURVEY_REQUIRED.value and not parcel.get("geometry"):
        raise HTTPException(status_code=409, detail="Parcel geometry is required before survey")
    elif target == ApplicationStatus.SURVEYED.value and not application.get("survey", {}).get("report_id"):
        raise HTTPException(status_code=409, detail="A survey report is required")
    elif target in {ApplicationStatus.LEGAL_REVIEW.value, ApplicationStatus.APPROVED.value}:
        unverified = [
            doc["document_type"]
            for doc in documents
            if doc.get("required") and doc.get("status") != "verified"
        ]
        if unverified:
            raise HTTPException(status_code=409, detail=f"Documents require verification: {', '.join(unverified)}")
        if target == ApplicationStatus.APPROVED.value and application.get("registrar_review", {}).get("decision") != "approved":
            raise HTTPException(status_code=409, detail="An approved registrar review is required")
