from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import (
    get_current_user,
    require_roles,
)

from db.database import get_db

from schemas.technician import (
    TechnicianAssignmentCreate,
    TechnicianAssignmentResponse,
    TechnicianAssignmentStatusUpdate,
    TechnicianCreate,
    TechnicianReassignment,
    TechnicianResponse,
    TechnicianSkillCreate,
    TechnicianSkillResponse,
    TechnicianUpdate,
)

from services.technician_service import TechnicianService

from utils.enums import UserRole


router = APIRouter(
    prefix="/technicians",
    tags=["Field Technicians"],
)

service = TechnicianService()


@router.post(
    "/",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_technician(
    data: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
):
    return service.create(
        db,
        data,
    )


@router.get(
    "/",
    response_model=list[TechnicianResponse],
)
def get_technicians(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_all(db)


@router.get(
    "/{technician_id}",
    response_model=TechnicianResponse,
)
def get_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get(
        db,
        technician_id,
    )


@router.put(
    "/{technician_id}",
    response_model=TechnicianResponse,
)
def update_technician(
    technician_id: int,
    data: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.update(
        db,
        technician_id,
        data,
    )


@router.post(
    "/{technician_id}/skills",
    response_model=TechnicianSkillResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_skill(
    technician_id: int,
    data: TechnicianSkillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.add_skill(
        db,
        technician_id,
        data,
    )


@router.get(
    "/{technician_id}/skills",
    response_model=list[TechnicianSkillResponse],
)
def get_skills(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_skills(
        db,
        technician_id,
    )


@router.post(
    "/assignments",
    response_model=TechnicianAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_technician(
    data: TechnicianAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.assign(
        db,
        data,
        assigned_by=current_user.id,
    )


@router.patch(
    "/assignments/{assignment_id}/reassign",
    response_model=TechnicianAssignmentResponse,
)
def reassign_technician(
    assignment_id: int,
    data: TechnicianReassignment,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.reassign(
        db,
        assignment_id,
        data,
        assigned_by=current_user.id,
    )


@router.patch(
    "/assignments/{assignment_id}/status",
    response_model=TechnicianAssignmentResponse,
)
def update_assignment_status(
    assignment_id: int,
    data: TechnicianAssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.update_assignment_status(
        db,
        assignment_id,
        data,
    )


@router.get(
    "/{technician_id}/workload",
)
def technician_workload(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.workload(
        db,
        technician_id,
    )


@router.get(
    "/{technician_id}/completed-jobs",
    response_model=list[TechnicianAssignmentResponse],
)
def completed_jobs(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.completed_jobs(
        db,
        technician_id,
    )


@router.get(
    "/{technician_id}/pending-jobs",
    response_model=list[TechnicianAssignmentResponse],
)
def pending_jobs(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.pending_jobs(
        db,
        technician_id,
    )