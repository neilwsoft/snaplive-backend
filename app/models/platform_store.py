from datetime import datetime
from typing import Optional, Dict, Annotated, Any
from enum import Enum
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
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


class ConnectionStatus(str, Enum):
    """Store connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class SyncStatus(str, Enum):
    """Sync status"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"


class PlatformStoreConfig(BaseModel):
    """Platform-specific configuration"""
    # Sync settings
    auto_sync_inventory: bool = Field(default=True)
    auto_sync_orders: bool = Field(default=True)
    auto_sync_products: bool = Field(default=True)

    # RTMP streaming settings
    rtmp_enabled: bool = Field(default=False)
    rtmp_url: Optional[str] = None
    rtmp_stream_key: Optional[str] = None

    # Rate limiting
    max_requests_per_minute: int = Field(default=60)

    # Other platform-specific settings
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class PlatformStore(BaseModel):
    """Platform store connection model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    seller_id: PyObjectId  # Reference to Seller model

    # Platform information
    platform: Platform
    store_id: str  # Platform-specific store ID
    store_name: str  # Store name on the platform
    store_url: Optional[str] = None

    # Connection status
    connection_status: ConnectionStatus = Field(default=ConnectionStatus.PENDING)
    connection_error: Optional[str] = None

    # Sync status
    last_sync_at: Optional[datetime] = None
    last_sync_status: SyncStatus = Field(default=SyncStatus.IDLE)
    last_sync_error: Optional[str] = None

    # Sync statistics
    total_syncs: int = Field(default=0)
    successful_syncs: int = Field(default=0)
    failed_syncs: int = Field(default=0)

    # Configuration
    config: PlatformStoreConfig = Field(default_factory=PlatformStoreConfig)

    # Credentials reference
    credential_id: Optional[PyObjectId] = None  # Reference to PlatformCredential

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
