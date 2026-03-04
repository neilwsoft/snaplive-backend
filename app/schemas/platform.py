from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from app.models.platform_store import Platform


class PlatformInfo(BaseModel):
    """Platform information schema"""
    platform: Platform
    display_name: str
    description: str
    logo_url: Optional[str] = None
    is_available: bool = Field(default=True)
    requires_oauth: bool = Field(default=False)
    supports_rtmp: bool = Field(default=False)
    supports_inventory_sync: bool = Field(default=True)
    supports_order_sync: bool = Field(default=True)
    supports_product_sync: bool = Field(default=True)
    supports_stream_data: bool = Field(default=False)

    # Connection requirements
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)

    # Rate limits
    rate_limit_per_minute: int = Field(default=60)

    # Documentation
    documentation_url: Optional[str] = None
    setup_guide_url: Optional[str] = None


class PlatformListResponse(BaseModel):
    """Response for list of available platforms"""
    platforms: List[PlatformInfo]
    total: int


class PlatformStatsResponse(BaseModel):
    """Statistics for a specific platform"""
    platform: Platform
    total_stores: int = Field(default=0, ge=0)
    connected_stores: int = Field(default=0, ge=0)
    active_streams: int = Field(default=0, ge=0)
    total_syncs_today: int = Field(default=0, ge=0)
    successful_syncs_today: int = Field(default=0, ge=0)
    failed_syncs_today: int = Field(default=0, ge=0)
    last_sync_at: Optional[datetime] = None
