from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.device import Device
from models.device_sim_mapping import DeviceSIMMapping

from repositories.customer_repository import CustomerRepository
from repositories.device_repository import DeviceRepository
from repositories.device_sim_mapping_repository import (
    DeviceSIMMappingRepository,
)
from repositories.sim_repository import SIMRepository

from utils.enums import DeviceStatus, DeviceType, SIMStatus


class DeviceService:

    def __init__(self):
        self.device_repository = DeviceRepository()
        self.mapping_repository = DeviceSIMMappingRepository()

    # =========================================================
    # CUSTOMER VALIDATION
    # =========================================================

    def _validate_customer(
        self,
        db: Session,
        customer_id: int,
    ):
        customer_repository = CustomerRepository(db)

        customer = customer_repository.get_by_id(
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer is inactive",
            )

        return customer

    # =========================================================
    # GET DEVICE
    # =========================================================

    def _get_device(
        self,
        db: Session,
        device_id: int,
    ) -> Device:

        device = self.device_repository.get_by_id(
            db,
            device_id,
        )

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        return device

    # =========================================================
    # CREATE DEVICE
    # =========================================================

    def create(
        self,
        db: Session,
        imei: str,
        model: str,
        manufacturer: str,
        device_type: DeviceType,
        customer_id: int | None = None,
    ) -> Device:

        existing_device = self.device_repository.get_by_imei(
            db,
            imei,
        )

        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device with this IMEI already exists",
            )

        if customer_id is not None:
            self._validate_customer(
                db,
                customer_id,
            )

        device = Device(
            imei=imei,
            model=model,
            manufacturer=manufacturer,
            device_type=device_type,
            status=DeviceStatus.ACTIVE,
            customer_id=customer_id,
        )

        return self.device_repository.create(
            db,
            device,
        )

    # =========================================================
    # GET DEVICE
    # =========================================================

    def get(
        self,
        db: Session,
        device_id: int,
    ) -> Device:

        return self._get_device(
            db,
            device_id,
        )

    # =========================================================
    # LIST DEVICES
    # =========================================================

    def list(
        self,
        db: Session,
        search: str | None = None,
        device_type: DeviceType | None = None,
        status: DeviceStatus | None = None,
        customer_id: int | None = None,
    ):

        return self.device_repository.list(
            db=db,
            search=search,
            device_type=device_type,
            status=status,
            customer_id=customer_id,
        )

    # =========================================================
    # UPDATE DEVICE
    # =========================================================

    def update(
        self,
        db: Session,
        device_id: int,
        imei: str | None = None,
        model: str | None = None,
        manufacturer: str | None = None,
        device_type: DeviceType | None = None,
        customer_id: int | None = None,
    ) -> Device:

        device = self._get_device(
            db,
            device_id,
        )

        # -----------------------------------------------------
        # Update IMEI
        # -----------------------------------------------------

        if imei is not None and imei != device.imei:

            existing_device = self.device_repository.get_by_imei(
                db,
                imei,
            )

            if (
                existing_device
                and existing_device.id != device.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Device with this IMEI already exists",
                )

            device.imei = imei

        # -----------------------------------------------------
        # Update model
        # -----------------------------------------------------

        if model is not None:
            device.model = model

        # -----------------------------------------------------
        # Update manufacturer
        # -----------------------------------------------------

        if manufacturer is not None:
            device.manufacturer = manufacturer

        # -----------------------------------------------------
        # Update device type
        # -----------------------------------------------------

        if device_type is not None:
            device.device_type = device_type

        # -----------------------------------------------------
        # Update customer
        # -----------------------------------------------------

        if customer_id is not None:

            self._validate_customer(
                db,
                customer_id,
            )

            device.customer_id = customer_id

        return self.device_repository.update(
            db,
            device,
        )

    # =========================================================
    # ACTIVATE DEVICE
    # =========================================================

    def activate(
        self,
        db: Session,
        device_id: int,
    ) -> Device:

        device = self._get_device(
            db,
            device_id,
        )

        device.status = DeviceStatus.ACTIVE

        return self.device_repository.update(
            db,
            device,
        )

    # =========================================================
    # DEACTIVATE DEVICE
    # =========================================================

    def deactivate(
        self,
        db: Session,
        device_id: int,
    ) -> Device:

        device = self._get_device(
            db,
            device_id,
        )

        device.status = DeviceStatus.INACTIVE

        active_mapping = (
            self.mapping_repository.get_active_by_device(
                db,
                device_id,
            )
        )

        if active_mapping:
            self.mapping_repository.deactivate(
                db,
                active_mapping,
            )

        return self.device_repository.update(
            db,
            device,
        )

    # =========================================================
    # BLOCK DEVICE
    # =========================================================

    def block(
        self,
        db: Session,
        device_id: int,
    ) -> Device:

        device = self._get_device(
            db,
            device_id,
        )

        device.status = DeviceStatus.BLOCKED

        return self.device_repository.update(
            db,
            device,
        )

    # =========================================================
    # MARK DEVICE AS LOST
    # =========================================================

    def mark_lost(
        self,
        db: Session,
        device_id: int,
    ) -> Device:

        device = self._get_device(
            db,
            device_id,
        )

        device.status = DeviceStatus.LOST

        active_mapping = (
            self.mapping_repository.get_active_by_device(
                db,
                device_id,
            )
        )

        if active_mapping:
            self.mapping_repository.deactivate(
                db,
                active_mapping,
            )

        return self.device_repository.update(
            db,
            device,
        )

    # =========================================================
    # ASSIGN SIM
    # =========================================================

    def assign_sim(
        self,
        db: Session,
        device_id: int,
        sim_id: int,
    ) -> DeviceSIMMapping:

        # -----------------------------------------------------
        # Validate device
        # -----------------------------------------------------

        device = self._get_device(
            db,
            device_id,
        )

        # -----------------------------------------------------
        # Device must be active
        # -----------------------------------------------------

        if device.status != DeviceStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active devices can have a SIM assigned",
            )

        # -----------------------------------------------------
        # Device must have customer
        # -----------------------------------------------------

        if device.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device must be assigned to a customer first",
            )

        # -----------------------------------------------------
        # Validate device customer
        # -----------------------------------------------------

        self._validate_customer(
            db,
            device.customer_id,
        )

        # -----------------------------------------------------
        # Get SIM
        # -----------------------------------------------------

        sim_repository = SIMRepository(db)

        sim = sim_repository.get_by_id(
            sim_id,
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM not found",
            )

        # -----------------------------------------------------
        # SIM must be active
        # -----------------------------------------------------

        if sim.status != SIMStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active SIMs can be assigned to a device",
            )

        # -----------------------------------------------------
        # SIM and device must belong to same customer
        # -----------------------------------------------------

        if sim.customer_id != device.customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIM and device must belong to the same customer",
            )

        # -----------------------------------------------------
        # SIM cannot already belong to another device
        # -----------------------------------------------------

        active_sim_mapping = (
            self.mapping_repository.get_active_by_sim(
                db,
                sim_id,
            )
        )

        if active_sim_mapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SIM is already assigned to another active device",
            )

        # -----------------------------------------------------
        # Device cannot have two active SIMs
        # -----------------------------------------------------

        active_device_mapping = (
            self.mapping_repository.get_active_by_device(
                db,
                device_id,
            )
        )

        if active_device_mapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device already has an active SIM",
            )

        # -----------------------------------------------------
        # Create mapping
        # -----------------------------------------------------

        mapping = DeviceSIMMapping(
            device_id=device_id,
            sim_id=sim_id,
            assigned_at=datetime.now(timezone.utc),
            is_active=True,
        )

        return self.mapping_repository.create(
            db,
            mapping,
        )

    # =========================================================
    # UNASSIGN SIM
    # =========================================================

    def unassign_sim(
        self,
        db: Session,
        device_id: int,
    ) -> DeviceSIMMapping:

        self._get_device(
            db,
            device_id,
        )

        active_mapping = (
            self.mapping_repository.get_active_by_device(
                db,
                device_id,
            )
        )

        if not active_mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active SIM assigned to this device",
            )

        return self.mapping_repository.deactivate(
            db,
            active_mapping,
        )

    # =========================================================
    # GET CURRENT SIM
    # =========================================================

    def get_current_sim(
        self,
        db: Session,
        device_id: int,
    ) -> DeviceSIMMapping:

        self._get_device(
            db,
            device_id,
        )

        active_mapping = (
            self.mapping_repository.get_active_by_device(
                db,
                device_id,
            )
        )

        if not active_mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active SIM assigned to this device",
            )

        return active_mapping

    # =========================================================
    # SIM HISTORY
    # =========================================================

    def sim_history(
        self,
        db: Session,
        device_id: int,
    ):

        self._get_device(
            db,
            device_id,
        )

        return self.mapping_repository.get_history_by_device(
            db,
            device_id,
        )