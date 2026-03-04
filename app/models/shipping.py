"""
Shipping Models

Models for saved shipper and recipient addresses used in order processing.
"""

from datetime import datetime
from typing import Optional, Annotated
from enum import Enum
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class AddressType(str, Enum):
    """Address type enum"""
    SHIPPER = "shipper"
    RECIPIENT = "recipient"


class SavedAddress(BaseModel):
    """
    Saved address model for shippers and recipients.
    Used in order processing for quick address selection.
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # Owner (seller) who saved this address
    seller_id: Optional[PyObjectId] = None

    # Address type
    address_type: AddressType

    # Address label for quick identification
    label: Optional[str] = None  # e.g., "Main Warehouse", "Home", "Office"

    # Contact information
    name: str = Field(..., description="Contact name")
    contact_number: str = Field(..., description="Phone number")
    email: Optional[str] = None

    # Address details
    address_line1: str = Field(..., description="Street address")
    address_line2: Optional[str] = None
    city: str
    province: str
    postal_code: str
    country: str = Field(default="China")

    # Default flag
    is_default: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True


class LogisticsProvider(BaseModel):
    """
    Logistics provider model for e-waybill generation.
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # Provider info
    code: str = Field(..., description="Provider code (e.g., 'sf', 'yto')")
    name: str = Field(..., description="Provider name in English")
    name_zh: str = Field(..., description="Provider name in Chinese")

    # Service types offered
    service_types: list[str] = Field(
        default_factory=lambda: ["standard", "express", "economy"],
        description="Available service types"
    )

    # Status
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
