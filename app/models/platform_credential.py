from datetime import datetime
from typing import Optional, Dict, Annotated
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


# Pydantic v2 compatible ObjectId type
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class Platform(str, Enum):
    """E-commerce platform enum"""
    TAOBAO = "taobao"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"


class CredentialType(str, Enum):
    """Credential type"""
    OAUTH = "oauth"
    API_KEY = "api_key"
    SESSION_KEY = "session_key"


class PlatformCredential(BaseModel):
    """Platform API credentials model - stores encrypted credentials"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    seller_id: PyObjectId  # Reference to Seller model
    platform: Platform

    # Credential type
    credential_type: CredentialType = Field(default=CredentialType.API_KEY)

    # Encrypted credentials (should be encrypted at rest)
    # For OAuth
    access_token: Optional[str] = None  # Encrypted
    refresh_token: Optional[str] = None  # Encrypted
    token_expires_at: Optional[datetime] = None

    # For API Key
    api_key: Optional[str] = None  # Encrypted
    api_secret: Optional[str] = None  # Encrypted
    app_key: Optional[str] = None  # For Taobao
    session_key: Optional[str] = None  # For Taobao session

    # Additional platform-specific fields
    extra_fields: Dict[str, str] = Field(default_factory=dict)  # All encrypted

    # Status
    is_valid: bool = Field(default=True)
    is_expired: bool = Field(default=False)
    last_validated_at: Optional[datetime] = None
    validation_error: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
