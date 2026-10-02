from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import KYCStatus


class CustomerCreate(BaseModel):
    user_id: int = Field(gt=0)

    customer_number: str = Field(
        min_length=3,
        max_length=50,
    )

    address_line1: str | None = Field(
        default=None,
        max_length=255,
    )

    address_line2: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    kyc_status: KYCStatus = KYCStatus.PENDING


class CustomerUpdate(BaseModel):
    address_line1: str | None = Field(
        default=None,
        max_length=255,
    )

    address_line2: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    kyc_status: KYCStatus | None = None


class CustomerResponse(BaseModel):
    id: int
    user_id: int
    customer_number: str

    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str | None

    kyc_status: KYCStatus

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )