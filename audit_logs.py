from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from db.database import get_db
from schemas.audit_log import AuditLogResponse
from services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)

service = AuditLogService()


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    action: str | None = None,
    entity: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    logs, _, _ = service.get_all(
        db=db,
        page=page,
        page_size=page_size,
        action=action,
        entity=entity,
        user_id=user_id,
    )

    return logs


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    audit_log = service.get_by_id(
        db,
        audit_log_id,
    )

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return audit_log