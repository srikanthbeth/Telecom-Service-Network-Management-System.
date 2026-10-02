
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.network_equipment import NetworkEquipment
from repositories.network_equipment_repository import (
    NetworkEquipmentRepository,
)
from utils.enums import EquipmentHealth, EquipmentType, NetworkStatus


class NetworkEquipmentService:

    def __init__(self):
        self.repository = NetworkEquipmentRepository()

    def create(
        self,
        db: Session,
        equipment_code: str,
        equipment_name: str,
        equipment_type: EquipmentType,
        manufacturer: str | None,
        model_number: str | None,
        serial_number: str | None,
        tower_id: int | None,
        location: str | None,
        installation_date,
        maintenance_schedule,
        cpu_usage: float,
        memory_usage: float,
        network_status: NetworkStatus,
        health_status: EquipmentHealth,
        last_heartbeat,
        downtime_minutes: int,
        description: str | None,
        created_by: int,
    ):
        existing = self.repository.get_by_code(
            db,
            equipment_code,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Equipment code already exists",
            )

        if serial_number:
            existing_serial = self.repository.get_by_serial_number(
                db,
                serial_number,
            )

            if existing_serial:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Serial number already exists",
                )

        equipment = NetworkEquipment(
            equipment_code=equipment_code,
            equipment_name=equipment_name,
            equipment_type=equipment_type.value,
            manufacturer=manufacturer,
            model_number=model_number,
            serial_number=serial_number,
            tower_id=tower_id,
            location=location,
            installation_date=installation_date,
            maintenance_schedule=maintenance_schedule,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            network_status=network_status.value,
            health_status=health_status.value,
            last_heartbeat=last_heartbeat,
            downtime_minutes=downtime_minutes,
            description=description,
            created_by=created_by,
        )

        return self.repository.create(
            db,
            equipment,
        )

    def get(
        self,
        db: Session,
        equipment_id: int,
    ):
        equipment = self.repository.get_by_id(
            db,
            equipment_id,
        )

        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Network equipment not found",
            )

        return equipment

    def list(
        self,
        db: Session,
        equipment_type: EquipmentType | None = None,
        network_status: NetworkStatus | None = None,
        health_status: EquipmentHealth | None = None,
        tower_id: int | None = None,
        search: str | None = None,
    ):
        return self.repository.list(
            db=db,
            equipment_type=equipment_type,
            network_status=network_status,
            health_status=health_status,
            tower_id=tower_id,
            search=search,
        )

    def update(
        self,
        db: Session,
        equipment_id: int,
        values: dict,
    ):
        equipment = self.get(
            db,
            equipment_id,
        )

        if "serial_number" in values:
            serial_number = values["serial_number"]

            if serial_number:
                existing = (
                    self.repository.get_by_serial_number(
                        db,
                        serial_number,
                    )
                )

                if existing and existing.id != equipment_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Serial number already exists",
                    )

        if "equipment_type" in values:
            values["equipment_type"] = (
                values["equipment_type"].value
            )

        return self.repository.update(
            db,
            equipment,
            values,
        )

    def update_status(
        self,
        db: Session,
        equipment_id: int,
        network_status: NetworkStatus,
    ):
        equipment = self.get(
            db,
            equipment_id,
        )

        values = {
            "network_status": network_status.value,
        }

        if network_status == NetworkStatus.OFFLINE:
            if not equipment.last_heartbeat:
                equipment.last_heartbeat = datetime.utcnow()

        return self.repository.update(
            db,
            equipment,
            values,
        )

    def update_health(
        self,
        db: Session,
        equipment_id: int,
        health_status: EquipmentHealth,
    ):
        equipment = self.get(
            db,
            equipment_id,
        )

        return self.repository.update(
            db,
            equipment,
            {
                "health_status": health_status.value,
            },
        )

    def delete(
        self,
        db: Session,
        equipment_id: int,
    ):
        equipment = self.get(
            db,
            equipment_id,
        )

        self.repository.delete(
            db,
            equipment,
        )

