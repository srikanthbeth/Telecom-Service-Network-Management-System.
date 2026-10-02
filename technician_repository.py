from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.technician import Technician
from models.technician_assignment import TechnicianAssignment
from models.technician_skill import TechnicianSkill
from utils.enums import TechnicianJobStatus


class TechnicianRepository:

    def create(
        self,
        db: Session,
        technician: Technician,
    ):
        db.add(technician)
        db.flush()
        return technician

    def get_by_id(
        self,
        db: Session,
        technician_id: int,
    ):
        return db.get(
            Technician,
            technician_id,
        )

    def get_by_employee_id(
        self,
        db: Session,
        employee_id: str,
    ):
        statement = select(Technician).where(
            Technician.employee_id == employee_id
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
    ):
        statement = select(Technician).where(
            Technician.user_id == user_id
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_all(
        self,
        db: Session,
    ):
        statement = select(Technician).order_by(
            Technician.id.desc()
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def update(
        self,
        db: Session,
        technician: Technician,
        values: dict,
    ):
        for key, value in values.items():
            setattr(
                technician,
                key,
                value,
            )

        db.flush()

        return technician

    def add_skill(
        self,
        db: Session,
        skill: TechnicianSkill,
    ):
        db.add(skill)
        db.flush()
        return skill

    def get_skill(
        self,
        db: Session,
        technician_id: int,
        skill_name: str,
    ):
        statement = select(TechnicianSkill).where(
            TechnicianSkill.technician_id
            == technician_id,
            TechnicianSkill.skill_name
            == skill_name,
        )

        return db.execute(
            statement
        ).scalar_one_or_none()

    def get_skills(
        self,
        db: Session,
        technician_id: int,
    ):
        statement = select(TechnicianSkill).where(
            TechnicianSkill.technician_id
            == technician_id
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def create_assignment(
        self,
        db: Session,
        assignment: TechnicianAssignment,
    ):
        db.add(assignment)
        db.flush()
        return assignment

    def get_assignment(
        self,
        db: Session,
        assignment_id: int,
    ):
        return db.get(
            TechnicianAssignment,
            assignment_id,
        )

    def get_pending_jobs(
        self,
        db: Session,
        technician_id: int,
    ):
        statement = select(
            TechnicianAssignment
        ).where(
            TechnicianAssignment.technician_id
            == technician_id,
            TechnicianAssignment.status.in_(
                [
                    TechnicianJobStatus.ASSIGNED.value,
                    TechnicianJobStatus.IN_PROGRESS.value,
                ]
            ),
        ).order_by(
            TechnicianAssignment.assigned_at.asc()
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def get_completed_jobs(
        self,
        db: Session,
        technician_id: int,
    ):
        statement = select(
            TechnicianAssignment
        ).where(
            TechnicianAssignment.technician_id
            == technician_id,
            TechnicianAssignment.status
            == TechnicianJobStatus.COMPLETED.value,
        ).order_by(
            TechnicianAssignment.completed_at.desc()
        )

        return list(
            db.execute(statement).scalars().all()
        )

    def get_workload(
        self,
        db: Session,
        technician_id: int,
    ):
        statement = select(
            func.count(TechnicianAssignment.id)
        ).where(
            TechnicianAssignment.technician_id
            == technician_id,
            TechnicianAssignment.status.in_(
                [
                    TechnicianJobStatus.ASSIGNED.value,
                    TechnicianJobStatus.IN_PROGRESS.value,
                ]
            ),
        )

        return db.execute(
            statement
        ).scalar_one()