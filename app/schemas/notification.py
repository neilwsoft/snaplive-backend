from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from app.models.notification import NotificationType, NotificationStatus


class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    notification_type: NotificationType
    recipient_email: EmailStr
    recipient_name: str
    language: str
    order_id: str
    order_number: str


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: str
    notification_type: NotificationType
    recipient_email: EmailStr
    recipient_name: str
    language: str
    order_id: str
    order_number: str
    subject: str
    status: NotificationStatus
    retry_count: int
    created_at: datetime
    sent_at: Optional[datetime]
    failed_at: Optional[datetime]
    last_error: Optional[str]

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for notification list response"""
    notifications: list[NotificationResponse]
    total: int
    page: int
    page_size: int


class TestNotificationRequest(BaseModel):
    """Schema for testing notification endpoint"""
    notification_type: NotificationType
    language: str = "ko"
    recipient_email: EmailStr
    recipient_name: str
