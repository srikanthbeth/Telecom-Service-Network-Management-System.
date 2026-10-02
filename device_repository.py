from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.device import Device
from utils.enums import DeviceStatus, DeviceType


class DeviceRepository:

    def get_by_id(
        self,
        db: Session,
        device_id: int,
    ) -> Device | None:
        return db.get(Device, device_id)

    def get_by_imei(
        self,
        db: Session,
        imei: str,
    ) -> Device | None:
        statement = select(Device).where(
            Device.imei == imei
        )

        return db.scalar(statement)

    def create(
        self,
        db: Session,
        device: Device,
    ) -> Device:
        db.add(device)
        db.flush()
        db.refresh(device)

        return device

    def update(
        self,
        db: Session,
        device: Device,
    ) -> Device:
        db.flush()
        db.refresh(device)

        return device

    def list(
        self,
        db: Session,
        search: str | None = None,
        device_type: DeviceType | None = None,
        status: DeviceStatus | None = None,
        customer_id: int | None = None,
    ) -> List[Device]:

        statement = select(Device)

        if search:
            search_value = f"%{search}%"

            statement = statement.where(
                (Device.imei.ilike(search_value))
                | (Device.model.ilike(search_value))
                | (Device.manufacturer.ilike(search_value))
            )

        if device_type:
            statement = statement.where(
                Device.device_type == device_type
            )

        if status:
            statement = statement.where(
                Device.status == status
            )

        if customer_id:
            statement = statement.where(
                Device.customer_id == customer_id
            )

        statement = statement.order_by(
            Device.id.desc()
        )

        return list(
            db.scalars(statement).all()
        )