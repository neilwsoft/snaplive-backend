from datetime import datetime
from typing import Optional, Dict, Any, Annotated
from enum import Enum
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


class NotificationType(str, Enum):
    """Notification type enum"""
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"


class NotificationStatus(str, Enum):
    """Notification delivery status enum"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationLog(BaseModel):
    """Notification log model for tracking sent notifications"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # Notification details
    notification_type: NotificationType
    recipient_email: EmailStr
    recipient_name: str
    language: str  # "ko" or "zh"

    # Order reference
    order_id: PyObjectId
    order_number: str

    # Email details
    subject: str
    body_html: str
    body_text: Optional[str] = None

    # Status tracking
    status: NotificationStatus = Field(default=NotificationStatus.PENDING)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    # Error tracking
    last_error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
