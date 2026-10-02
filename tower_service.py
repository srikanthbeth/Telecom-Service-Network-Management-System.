from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.tower import Tower, TowerStatus, TowerType
from repositories.tower_repository import TowerRepository
from schemas.tower import TowerCreate, TowerUpdate


class TowerService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = TowerRepository(db)

    def create_tower(
        self,
        data: TowerCreate,
    ) -> Tower:

        existing = self.repository.get_by_code(
            data.tower_code
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tower code already exists",
            )

        tower = Tower(
            tower_code=data.tower_code,
            tower_name=data.tower_name,
            tower_type=data.tower_type,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
            coverage_area=data.coverage_area,
            capacity=data.capacity,
            status=data.status,
        )

        return self.repository.create(tower)

    def get_tower(
        self,
        tower_id: int,
    ) -> Tower:

        tower = self.repository.get_by_id(
            tower_id
        )

        if not tower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tower not found",
            )

        return tower

    def list_towers(
        self,
        status_value: TowerStatus | None = None,
        tower_type: TowerType | None = None,
        search: str | None = None,
    ) -> list[Tower]:

        return self.repository.list(
            status=status_value,
            tower_type=tower_type,
            search=search,
        )

    def update_tower(
        self,
        tower_id: int,
        data: TowerUpdate,
    ) -> Tower:

        tower = self.get_tower(tower_id)

        updates = data.model_dump(
            exclude_unset=True
        )

        for field, value in updates.items():
            setattr(tower, field, value)

        return self.repository.update(tower)

    def update_status(
        self,
        tower_id: int,
        status_value: TowerStatus,
    ) -> Tower:

        tower = self.get_tower(tower_id)

        tower.status = status_value

        return self.repository.update(tower)

    def delete_tower(
        self,
        tower_id: int,
    ) -> None:

        tower = self.get_tower(tower_id)

        self.repository.delete(tower)