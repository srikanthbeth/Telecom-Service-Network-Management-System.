from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.technician import Technician
from models.technician_assignment import TechnicianAssignment
from models.technician_skill import TechnicianSkill

from repositories.technician_repository import (
    TechnicianRepository,
)

from schemas.technician import (
    TechnicianAssignmentCreate,
    TechnicianAssignmentStatusUpdate,
    TechnicianCreate,
    TechnicianReassignment,
    TechnicianSkillCreate,
    TechnicianUpdate,
)

from utils.enums import (
    TechnicianAvailability,
    TechnicianJobStatus,
)


class TechnicianService:

    def __init__(self):
        self.repository = TechnicianRepository()

    def create(
        self,
        db: Session,
        data: TechnicianCreate,
    ) -> Technician:

        existing_employee = (
            self.repository.get_by_employee_id(
                db,
                data.employee_id,
            )
        )

        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee ID already exists",
            )

        existing_user = (
            self.repository.get_by_user_id(
                db,
                data.user_id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already registered as a technician",
            )

        technician = Technician(
            user_id=data.user_id,
            employee_id=data.employee_id,
            full_name=data.full_name,
            phone=data.phone,
            availability=data.availability.value,
            latitude=data.latitude,
            longitude=data.longitude,
            service_area=data.service_area,
            address=data.address,
        )

        self.repository.create(
            db,
            technician,
        )

        db.commit()
        db.refresh(technician)

        return technician

    def get(
        self,
        db: Session,
        technician_id: int,
    ) -> Technician:

        technician = self.repository.get_by_id(
            db,
            technician_id,
        )

        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician not found",
            )

        return technician

    def get_all(
        self,
        db: Session,
    ):
        return self.repository.get_all(db)

    def update(
        self,
        db: Session,
        technician_id: int,
        data: TechnicianUpdate,
    ) -> Technician:

        technician = self.get(
            db,
            technician_id,
        )

        values = data.model_dump(
            exclude_unset=True
        )

        if "availability" in values:
            values["availability"] = (
                values["availability"].value
            )

        self.repository.update(
            db,
            technician,
            values,
        )

        db.commit()
        db.refresh(technician)

        return technician

    def add_skill(
        self,
        db: Session,
        technician_id: int,
        data: TechnicianSkillCreate,
    ):

        self.get(
            db,
            technician_id,
        )

        existing = self.repository.get_skill(
            db,
            technician_id,
            data.skill_name,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Skill already assigned to technician",
            )

        skill = TechnicianSkill(
            technician_id=technician_id,
            skill_name=data.skill_name,
        )

        self.repository.add_skill(
            db,
            skill,
        )

        db.commit()
        db.refresh(skill)

        return skill

    def get_skills(
        self,
        db: Session,
        technician_id: int,
    ):

        self.get(
            db,
            technician_id,
        )

        return self.repository.get_skills(
            db,
            technician_id,
        )

    def assign(
        self,
        db: Session,
        data: TechnicianAssignmentCreate,
        assigned_by: int | None = None,
    ):

        technician = self.get(
            db,
            data.technician_id,
        )

        if technician.availability == (
            TechnicianAvailability.ON_LEAVE.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Technician is on leave",
            )

        if technician.availability == (
            TechnicianAvailability.UNAVAILABLE.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Technician is unavailable",
            )

        assignment = TechnicianAssignment(
            technician_id=data.technician_id,
            customer_id=data.customer_id,
            job_type=data.job_type,
            job_reference_id=data.job_reference_id,
            description=data.description,
            status=TechnicianJobStatus.ASSIGNED.value,
            assigned_by=assigned_by,
        )

        self.repository.create_assignment(
            db,
            assignment,
        )

        technician.availability = (
            TechnicianAvailability.BUSY.value
        )

        db.commit()
        db.refresh(assignment)

        return assignment

    def reassign(
        self,
        db: Session,
        assignment_id: int,
        data: TechnicianReassignment,
        assigned_by: int | None = None,
    ):

        assignment = self.repository.get_assignment(
            db,
            assignment_id,
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician assignment not found",
            )

        new_technician = self.get(
            db,
            data.technician_id,
        )

        if new_technician.availability in [
            TechnicianAvailability.ON_LEAVE.value,
            TechnicianAvailability.UNAVAILABLE.value,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Technician is not available for assignment",
            )

        old_technician = self.get(
            db,
            assignment.technician_id,
        )

        old_technician.availability = (
            TechnicianAvailability.AVAILABLE.value
        )

        assignment.technician_id = (
            new_technician.id
        )

        assignment.assigned_by = assigned_by
        assignment.assigned_at = (
            datetime.now(timezone.utc)
        )

        assignment.status = (
            TechnicianJobStatus.ASSIGNED.value
        )

        new_technician.availability = (
            TechnicianAvailability.BUSY.value
        )

        db.commit()
        db.refresh(assignment)

        return assignment

    def update_assignment_status(
        self,
        db: Session,
        assignment_id: int,
        data: TechnicianAssignmentStatusUpdate,
    ):

        assignment = self.repository.get_assignment(
            db,
            assignment_id,
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Technician assignment not found",
            )

        assignment.status = data.status.value

        if data.status == TechnicianJobStatus.IN_PROGRESS:
            assignment.started_at = (
                datetime.now(timezone.utc)
            )

        elif data.status == TechnicianJobStatus.COMPLETED:
            assignment.completed_at = (
                datetime.now(timezone.utc)
            )

            technician = self.get(
                db,
                assignment.technician_id,
            )

            technician.availability = (
                TechnicianAvailability.AVAILABLE.value
            )

        db.commit()
        db.refresh(assignment)

        return assignment

    def workload(
        self,
        db: Session,
        technician_id: int,
    ):

        self.get(
            db,
            technician_id,
        )

        pending = self.repository.get_pending_jobs(
            db,
            technician_id,
        )

        completed = self.repository.get_completed_jobs(
            db,
            technician_id,
        )

        return {
            "technician_id": technician_id,
            "pending_jobs": len(pending),
            "completed_jobs": len(completed),
            "total_workload": len(pending),
        }

    def pending_jobs(
        self,
        db: Session,
        technician_id: int,
    ):

        self.get(
            db,
            technician_id,
        )

        return self.repository.get_pending_jobs(
            db,
            technician_id,
        )

    def completed_jobs(
        self,
        db: Session,
        technician_id: int,
    ):

        self.get(
            db,
            technician_id,
        )

        return self.repository.get_completed_jobs(
            db,
            technician_id,
        )