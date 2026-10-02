import json

from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from repositories.audit_log_repository import AuditLogRepository


class AuditLogService:

    def __init__(self):
        self.repository = AuditLogRepository()

    def _serialize_value(self, value):
        if value is None:
            return None

        if isinstance(value, str):
            return value

        return json.dumps(
            value,
            default=str,
        )

    def create_log(
        self,
        db: Session,
        user_id: int | None,
        action: str,
        entity: str,
        entity_id: int | None = None,
        previous_value=None,
        new_value=None,
    ):
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            previous_value=self._serialize_value(
                previous_value
            ),
            new_value=self._serialize_value(
                new_value
            ),
        )

        return self.repository.create(
            db,
            audit_log,
        )

    def get_by_id(
        self,
        db: Session,
        audit_log_id: int,
    ):
        return self.repository.get_by_id(
            db,
            audit_log_id,
        )

    def get_all(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
        entity: str | None = None,
        user_id: int | None = None,
    ):
        return self.repository.get_all(
            db=db,
            page=page,
            page_size=page_size,
            action=action,
            entity=entity,
            user_id=user_id,
        )