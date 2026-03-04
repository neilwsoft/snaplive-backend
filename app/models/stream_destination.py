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
    CUSTOM = "custom"


class StreamProtocol(str, Enum):
    """Streaming protocol"""
    RTMP = "rtmp"
    RTMPS = "rtmps"
    SRT = "srt"
    WEBRTC = "webrtc"


class StreamStatus(str, Enum):
    """Stream destination status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    STREAMING = "streaming"
    ERROR = "error"
    DISABLED = "disabled"


class StreamQuality(str, Enum):
    """Stream quality preset"""
    LOW = "low"  # 480p
    MEDIUM = "medium"  # 720p
    HIGH = "high"  # 1080p
    ULTRA = "ultra"  # 4K


class StreamDestination(BaseModel):
    """RTMP stream destination model for multi-platform broadcasting"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # References
    store_id: Optional[PyObjectId] = None  # Reference to PlatformStore (if platform-specific)
    seller_id: PyObjectId  # Reference to Seller

    # Platform
    platform: Platform
    destination_name: str  # User-friendly name

    # Stream configuration
    protocol: StreamProtocol = Field(default=StreamProtocol.RTMP)
    rtmp_url: str  # e.g., "rtmp://live.taobao.com/live"
    stream_key: str  # Encrypted stream key

    # Optional backup URL
    backup_rtmp_url: Optional[str] = None
    backup_stream_key: Optional[str] = None

    # Quality settings
    quality: StreamQuality = Field(default=StreamQuality.HIGH)
    bitrate_kbps: int = Field(default=4000, ge=500, le=10000)
    fps: int = Field(default=30, ge=15, le=60)
    resolution_width: int = Field(default=1920)
    resolution_height: int = Field(default=1080)

    # Audio settings
    audio_bitrate_kbps: int = Field(default=128, ge=64, le=320)
    audio_sample_rate: int = Field(default=44100)

    # Status
    status: StreamStatus = Field(default=StreamStatus.INACTIVE)
    is_enabled: bool = Field(default=True)
    connection_error: Optional[str] = None

    # Streaming statistics
    total_streams: int = Field(default=0, ge=0)
    successful_streams: int = Field(default=0, ge=0)
    failed_streams: int = Field(default=0, ge=0)

    # Current stream info
    current_stream_id: Optional[str] = None  # LiveKit room name
    egress_id: Optional[str] = None  # LiveKit egress ID
    stream_started_at: Optional[datetime] = None
    stream_ended_at: Optional[datetime] = None

    # Performance metrics
    average_bitrate_kbps: Optional[float] = None
    dropped_frames_count: int = Field(default=0, ge=0)
    last_error_message: Optional[str] = None

    # Platform-specific settings
    platform_settings: Dict[str, any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
