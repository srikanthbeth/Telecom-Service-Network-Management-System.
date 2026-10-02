from sqlalchemy import select
from sqlalchemy.orm import Session

from models.audit_log import AuditLog


class AuditLogRepository:

    def create(
        self,
        db: Session,
        audit_log: AuditLog,
    ):
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    def get_by_id(
        self,
        db: Session,
        audit_log_id: int,
    ):
        statement = select(AuditLog).where(
            AuditLog.id == audit_log_id
        )

        return db.scalar(statement)

    def get_all(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
        entity: str | None = None,
        user_id: int | None = None,
    ):
        conditions = []

        if action:
            conditions.append(
                AuditLog.action == action
            )

        if entity:
            conditions.append(
                AuditLog.entity == entity
            )

        if user_id:
            conditions.append(
                AuditLog.user_id == user_id
            )

        count_statement = select(AuditLog).where(
            *conditions
        )

        all_logs = db.scalars(
            count_statement
        ).all()

        total = len(all_logs)

        offset = (page - 1) * page_size

        statement = (
            select(AuditLog)
            .where(*conditions)
            .order_by(
                AuditLog.timestamp.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        logs = db.scalars(statement).all()

        total_pages = (
            (total + page_size - 1) // page_size
            if total
            else 0
        )

        return logs, total, total_pages