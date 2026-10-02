
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.network_equipment import NetworkEquipment
from utils.enums import EquipmentHealth, EquipmentType, NetworkStatus


class NetworkEquipmentRepository:

    def create(
        self,
        db: Session,
        equipment: NetworkEquipment,
    ):
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        return equipment

    def get_by_id(
        self,
        db: Session,
        equipment_id: int,
    ):
        return (
            db.query(NetworkEquipment)
            .filter(NetworkEquipment.id == equipment_id)
            .first()
        )

    def get_by_code(
        self,
        db: Session,
        equipment_code: str,
    ):
        return (
            db.query(NetworkEquipment)
            .filter(
                NetworkEquipment.equipment_code == equipment_code
            )
            .first()
        )

    def get_by_serial_number(
        self,
        db: Session,
        serial_number: str,
    ):
        return (
            db.query(NetworkEquipment)
            .filter(
                NetworkEquipment.serial_number == serial_number
            )
            .first()
        )

    def list(
        self,
        db: Session,
        equipment_type: EquipmentType | None = None,
        network_status: NetworkStatus | None = None,
        health_status: EquipmentHealth | None = None,
        tower_id: int | None = None,
        search: str | None = None,
    ):
        query = db.query(NetworkEquipment)

        if equipment_type:
            query = query.filter(
                NetworkEquipment.equipment_type
                == equipment_type.value
            )

        if network_status:
            query = query.filter(
                NetworkEquipment.network_status
                == network_status.value
            )

        if health_status:
            query = query.filter(
                NetworkEquipment.health_status
                == health_status.value
            )

        if tower_id:
            query = query.filter(
                NetworkEquipment.tower_id == tower_id
            )

        if search:
            search_value = f"%{search}%"

            query = query.filter(
                or_(
                    NetworkEquipment.equipment_code.ilike(
                        search_value
                    ),
                    NetworkEquipment.equipment_name.ilike(
                        search_value
                    ),
                    NetworkEquipment.manufacturer.ilike(
                        search_value
                    ),
                    NetworkEquipment.model_number.ilike(
                        search_value
                    ),
                    NetworkEquipment.serial_number.ilike(
                        search_value
                    ),
                )
            )

        return (
            query
            .order_by(NetworkEquipment.id.desc())
            .all()
        )

    def update(
        self,
        db: Session,
        equipment: NetworkEquipment,
        values: dict,
    ):
        for key, value in values.items():
            setattr(equipment, key, value)

        db.commit()
        db.refresh(equipment)

        return equipment

    def delete(
        self,
        db: Session,
        equipment: NetworkEquipment,
    ):
        db.delete(equipment)
        db.commit()

