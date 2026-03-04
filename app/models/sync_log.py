from datetime import datetime
from typing import Optional, Dict, List, Annotated
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
    CUSTOM = "custom"


class SyncType(str, Enum):
    """Type of sync operation"""
    INVENTORY = "inventory"
    ORDERS = "orders"
    PRODUCTS = "products"
    STREAM_DATA = "stream_data"
    FULL_SYNC = "full_sync"


class SyncStatus(str, Enum):
    """Sync operation status"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncDirection(str, Enum):
    """Direction of sync"""
    PULL = "pull"  # From platform to SnapLive
    PUSH = "push"  # From SnapLive to platform
    BIDIRECTIONAL = "bidirectional"


class SyncResult(BaseModel):
    """Result details of a sync operation"""
    total_items: int = Field(default=0, ge=0)
    processed_items: int = Field(default=0, ge=0)
    successful_items: int = Field(default=0, ge=0)
    failed_items: int = Field(default=0, ge=0)
    skipped_items: int = Field(default=0, ge=0)

    # Details
    created_count: int = Field(default=0, ge=0)
    updated_count: int = Field(default=0, ge=0)
    deleted_count: int = Field(default=0, ge=0)

    # Errors
    errors: List[Dict[str, any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SyncLog(BaseModel):
    """Sync operation log model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # References
    store_id: PyObjectId  # Reference to PlatformStore
    seller_id: PyObjectId  # Reference to Seller
    platform: Platform

    # Sync details
    sync_type: SyncType
    sync_direction: SyncDirection = Field(default=SyncDirection.PULL)
    status: SyncStatus = Field(default=SyncStatus.STARTED)

    # Trigger
    triggered_by: str  # "auto", "manual", "webhook", "scheduled"
    triggered_by_user_id: Optional[PyObjectId] = None

    # Results
    result: Optional[SyncResult] = None

    # Error information
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, any]] = None
    stack_trace: Optional[str] = None

    # Performance metrics
    duration_seconds: Optional[float] = None
    api_calls_made: int = Field(default=0, ge=0)
    data_transferred_bytes: Optional[int] = None

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
