from sqlalchemy.orm import Session

from models.tower import Tower, TowerStatus, TowerType


class TowerRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, tower: Tower) -> Tower:
        self.db.add(tower)
        self.db.commit()
        self.db.refresh(tower)

        return tower

    def get_by_id(self, tower_id: int) -> Tower | None:
        return (
            self.db.query(Tower)
            .filter(Tower.id == tower_id)
            .first()
        )

    def get_by_code(
        self,
        tower_code: str,
    ) -> Tower | None:
        return (
            self.db.query(Tower)
            .filter(Tower.tower_code == tower_code)
            .first()
        )

    def list(
        self,
        status: TowerStatus | None = None,
        tower_type: TowerType | None = None,
        search: str | None = None,
    ) -> list[Tower]:

        query = self.db.query(Tower)

        if status:
            query = query.filter(
                Tower.status == status
            )

        if tower_type:
            query = query.filter(
                Tower.tower_type == tower_type
            )

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                (Tower.tower_code.ilike(search_value))
                | (Tower.tower_name.ilike(search_value))
                | (Tower.address.ilike(search_value))
            )

        return (
            query
            .order_by(Tower.id.desc())
            .all()
        )

    def update(self, tower: Tower) -> Tower:
        self.db.commit()
        self.db.refresh(tower)

        return tower

    def delete(self, tower: Tower) -> None:
        self.db.delete(tower)
        self.db.commit()