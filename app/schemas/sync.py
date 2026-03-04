from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from app.models.sync_log import (
    SyncType,
    SyncStatus,
    SyncDirection,
    SyncResult,
    Platform,
)


class SyncTrigger(BaseModel):
    """Schema for triggering a sync operation"""
    store_id: str
    sync_type: SyncType
    sync_direction: SyncDirection = Field(default=SyncDirection.PULL)
    force: bool = Field(default=False, description="Force sync even if recent sync exists")


class SyncResponse(BaseModel):
    """Schema for sync operation response"""
    id: str
    store_id: str
    seller_id: str
    platform: Platform

    # Sync details
    sync_type: SyncType
    sync_direction: SyncDirection
    status: SyncStatus

    # Trigger info
    triggered_by: str
    triggered_by_user_id: Optional[str]

    # Results
    result: Optional[SyncResult]

    # Error information
    error_message: Optional[str]
    error_details: Optional[Dict[str, any]]

    # Performance
    duration_seconds: Optional[float]
    api_calls_made: int

    # Timestamps
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SyncListResponse(BaseModel):
    """Schema for sync history list response"""
    syncs: List[SyncResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SyncStatusResponse(BaseModel):
    """Current sync status for a store"""
    store_id: str
    platform: Platform
    is_syncing: bool = Field(default=False)

    # Current sync (if any)
    current_sync: Optional[SyncResponse] = None

    # Last successful sync
    last_successful_sync: Optional[SyncResponse] = None

    # Statistics
    total_syncs_today: int = Field(default=0, ge=0)
    successful_syncs_today: int = Field(default=0, ge=0)
    failed_syncs_today: int = Field(default=0, ge=0)
    success_rate_today: float = Field(default=0, ge=0, le=100)

    # Next scheduled sync
    next_scheduled_sync_at: Optional[datetime] = None


class SyncHealthResponse(BaseModel):
    """Overall sync health across all stores"""
    total_stores: int = Field(default=0, ge=0)
    stores_syncing: int = Field(default=0, ge=0)
    stores_healthy: int = Field(default=0, ge=0)
    stores_with_errors: int = Field(default=0, ge=0)

    # Today's stats
    total_syncs_today: int = Field(default=0, ge=0)
    successful_syncs_today: int = Field(default=0, ge=0)
    failed_syncs_today: int = Field(default=0, ge=0)
    success_rate_today: float = Field(default=0, ge=0, le=100)

    # Platform breakdown
    platform_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    # Recent errors
    recent_errors: List[Dict[str, any]] = Field(default_factory=list)


class StreamingDestinationCreate(BaseModel):
    """Schema for creating a streaming destination"""
    store_id: Optional[str] = None
    platform: Platform
    destination_name: str

    # Stream configuration
    rtmp_url: str
    stream_key: str
    backup_rtmp_url: Optional[str] = None
    backup_stream_key: Optional[str] = None

    # Quality settings
    quality: str = Field(default="high")
    bitrate_kbps: int = Field(default=4000, ge=500, le=10000)
    fps: int = Field(default=30, ge=15, le=60)
    resolution_width: int = Field(default=1920)
    resolution_height: int = Field(default=1080)

    # Audio settings
    audio_bitrate_kbps: int = Field(default=128, ge=64, le=320)
    audio_sample_rate: int = Field(default=44100)

    # Platform-specific settings
    platform_settings: Dict[str, any] = Field(default_factory=dict)


class StreamingDestinationUpdate(BaseModel):
    """Schema for updating a streaming destination"""
    destination_name: Optional[str] = None
    rtmp_url: Optional[str] = None
    stream_key: Optional[str] = None
    backup_rtmp_url: Optional[str] = None
    backup_stream_key: Optional[str] = None
    quality: Optional[str] = None
    bitrate_kbps: Optional[int] = Field(default=None, ge=500, le=10000)
    fps: Optional[int] = Field(default=None, ge=15, le=60)
    is_enabled: Optional[bool] = None
    platform_settings: Optional[Dict[str, any]] = None


class StreamingDestinationResponse(BaseModel):
    """Schema for streaming destination response"""
    id: str
    store_id: Optional[str] = None
    seller_id: str
    platform: Platform
    destination_name: str

    # Stream configuration (without sensitive keys)
    rtmp_url: str
    has_backup: bool = Field(default=False)

    # Quality settings
    quality: str = "high"
    bitrate_kbps: int = 4000
    fps: int = 30
    resolution_width: int = 1920
    resolution_height: int = 1080

    # Status
    status: str = "inactive"
    is_enabled: bool = True
    connection_error: Optional[str] = None

    # Statistics
    total_streams: int = 0
    successful_streams: int = 0
    failed_streams: int = 0

    # Current stream
    is_streaming: bool = Field(default=False)
    stream_started_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StreamingDestinationListResponse(BaseModel):
    """Schema for streaming destination list response"""
    destinations: List[StreamingDestinationResponse]
    total: int


# --- Egress schemas ---

class StartEgressRequest(BaseModel):
    """Schema for starting egress on multiple destinations"""
    room_name: str
    destination_ids: List[str]


class EgressResult(BaseModel):
    """Result of an egress operation on a single destination"""
    destination_id: str
    success: bool
    egress_id: Optional[str] = None
    error: Optional[str] = None
    platform: Optional[str] = None


class EgressBatchResponse(BaseModel):
    """Response for batch egress operations"""
    results: List[EgressResult]


class EgressStatusInfo(BaseModel):
    """Egress status for a single destination"""
    egress_id: str
    status: str
    destination_id: Optional[str] = None
    platform: Optional[str] = None
    started_at: Optional[int] = None
    ended_at: Optional[int] = None
    error: Optional[str] = None


class EgressStatusResponse(BaseModel):
    """Response for egress status query"""
    egresses: List[EgressStatusInfo]
