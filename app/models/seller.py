from datetime import datetime
from typing import Optional, Dict, Annotated
from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Pydantic v2 compatible ObjectId type
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class BusinessInfo(BaseModel):
    """Business information for seller"""
    business_name: Dict[str, str]  # {"ko": "비즈니스명", "zh": "商家名称"}
    business_registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    business_type: Optional[str] = None  # e.g., "individual", "company"

    # Contact information
    contact_person: str
    contact_phone: str
    contact_email: EmailStr

    # Address
    business_address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: str = Field(default="KR")  # Default to Korea

    # Bank information
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_holder: Optional[str] = None


class Seller(BaseModel):
    """Seller model for MongoDB"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId  # Reference to User model

    # Business information
    business_info: BusinessInfo

    # Settings
    default_currency: str = Field(default="CNY")
    supported_languages: list[str] = Field(default=["ko", "zh"])

    # Platform preferences
    auto_sync_enabled: bool = Field(default=True)
    sync_interval_minutes: int = Field(default=5, ge=1, le=60)

    # Status
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
