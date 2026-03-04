from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.platform_store import (
    Platform,
    ConnectionStatus,
    SyncStatus,
    PlatformStoreConfig,
)


class StoreCreate(BaseModel):
    """Schema for creating a store connection"""
    platform: Platform
    store_id: str = Field(..., description="Platform-specific store ID")
    store_name: str = Field(..., description="Store name on the platform")
    store_url: Optional[str] = None

    # Credentials (will be encrypted)
    # Generic fields
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    # Taobao specific
    app_key: Optional[str] = None
    session_key: Optional[str] = None

    # Douyin specific
    client_key: Optional[str] = None
    client_secret: Optional[str] = None

    # Xiaohongshu specific
    app_id: Optional[str] = None
    app_secret: Optional[str] = None

    # OAuth tokens
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    # Configuration
    config: Optional[PlatformStoreConfig] = None


class StoreUpdate(BaseModel):
    """Schema for updating a store connection"""
    store_name: Optional[str] = None
    store_url: Optional[str] = None
    connection_status: Optional[ConnectionStatus] = None
    config: Optional[PlatformStoreConfig] = None

    # Update credentials
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    app_key: Optional[str] = None
    session_key: Optional[str] = None
    client_key: Optional[str] = None
    client_secret: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class StoreResponse(BaseModel):
    """Schema for store connection response"""
    id: str
    seller_id: str
    platform: Platform
    store_id: str
    store_name: str
    store_url: Optional[str] = None

    # Status
    connection_status: ConnectionStatus
    connection_error: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: SyncStatus

    # Statistics
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0

    # Configuration (without sensitive data)
    config: PlatformStoreConfig

    # Timestamps
    created_at: datetime
    updated_at: datetime
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class StoreListResponse(BaseModel):
    """Schema for store list response"""
    stores: list[StoreResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class StoreDashboardMetrics(BaseModel):
    """Dashboard metrics for a specific store"""
    store_id: str
    platform: Platform
    store_name: str

    # Connection health
    connection_status: ConnectionStatus
    last_sync_at: Optional[datetime]
    last_sync_error: Optional[str]
    api_calls_remaining: Optional[int] = None
    rate_limit_reset_at: Optional[datetime] = None

    # Sales metrics
    orders_today: int = Field(default=0, ge=0)
    orders_this_week: int = Field(default=0, ge=0)
    orders_this_month: int = Field(default=0, ge=0)
    revenue_today: float = Field(default=0, ge=0)
    revenue_this_week: float = Field(default=0, ge=0)
    revenue_this_month: float = Field(default=0, ge=0)
    average_order_value: float = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0, ge=0, le=100)

    # Inventory status
    total_products: int = Field(default=0, ge=0)
    in_stock_products: int = Field(default=0, ge=0)
    out_of_stock_products: int = Field(default=0, ge=0)
    low_stock_products: int = Field(default=0, ge=0)
    sync_conflicts: int = Field(default=0, ge=0)

    # Live streaming metrics
    active_streams: int = Field(default=0, ge=0)
    total_viewers_today: int = Field(default=0, ge=0)
    peak_concurrent_viewers: int = Field(default=0, ge=0)
    average_watch_time_minutes: float = Field(default=0, ge=0)
    engagement_rate: float = Field(default=0, ge=0, le=100)
    products_shown_in_stream: int = Field(default=0, ge=0)

    # Sync health
    sync_success_rate_24h: float = Field(default=0, ge=0, le=100)
    pending_sync_items: int = Field(default=0, ge=0)


class StoreConnectionTest(BaseModel):
    """Test store connection response"""
    success: bool
    platform: Platform
    store_id: str
    message: str
    details: Optional[Dict[str, Any]] = None
    tested_at: datetime = Field(default_factory=datetime.utcnow)
