"""Livestream Session Schemas

Pydantic schemas for livestream session API requests and responses.
"""

from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from app.models.livestream_session import SessionStatus


# Product Schemas

class SessionProductCreate(BaseModel):
    """Schema for adding a product to a session"""
    product_id: str
    product_name: Dict[str, str] = Field(..., description="Product name (en, ko)")
    sku: str
    unit_cost: float = Field(..., ge=0)
    available_at_start: int = Field(..., ge=0)
    category: Optional[str] = None
    image_url: Optional[str] = None


class SessionProductResponse(BaseModel):
    """Schema for product in session response"""
    product_id: str
    product_name: Dict[str, str]
    sku: str
    unit_cost: float
    available_at_start: int
    category: Optional[str] = None
    image_url: Optional[str] = None


# Stats Schemas

class SessionStatsResponse(BaseModel):
    """Schema for session statistics"""
    peak_viewers: int = 0
    total_viewers: int = 0
    products_sold: int = 0
    revenue: float = 0.0
    message_count: int = 0
    reaction_count: int = 0
    average_watch_time_seconds: int = 0


class SessionStatsUpdate(BaseModel):
    """Schema for updating session statistics"""
    peak_viewers: Optional[int] = Field(None, ge=0)
    total_viewers: Optional[int] = Field(None, ge=0)
    products_sold: Optional[int] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    message_count: Optional[int] = Field(None, ge=0)
    reaction_count: Optional[int] = Field(None, ge=0)
    average_watch_time_seconds: Optional[int] = Field(None, ge=0)


# Session Schemas

class LivestreamSessionCreate(BaseModel):
    """Schema for creating a livestream session"""
    seller_id: str
    room_name: str
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    products: List[SessionProductCreate] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    resolution: Optional[str] = None
    max_participants: int = Field(default=100, gt=0)
    enable_agent: bool = True


class LivestreamSessionUpdate(BaseModel):
    """Schema for updating a livestream session"""
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: Optional[SessionStatus] = None
    platforms: Optional[List[str]] = None
    category: Optional[str] = None
    resolution: Optional[str] = None
    max_participants: Optional[int] = Field(None, gt=0)
    enable_agent: Optional[bool] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    stats: Optional[SessionStatsUpdate] = None


class LivestreamSessionResponse(BaseModel):
    """Schema for livestream session response"""
    id: str = Field(..., alias="_id")
    seller_id: str
    room_name: str
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: SessionStatus
    products: List[SessionProductResponse]
    product_count: int
    platforms: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    resolution: Optional[str] = None
    max_participants: int
    enable_agent: bool
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    stats: SessionStatsResponse

    class Config:
        populate_by_name = True


class LivestreamSessionListResponse(BaseModel):
    """Schema for paginated session list"""
    items: List[LivestreamSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Start/End Session Schemas

class StartSessionRequest(BaseModel):
    """Schema for starting a session"""
    pass  # Just triggers status change


class EndSessionRequest(BaseModel):
    """Schema for ending a session"""
    stats: Optional[SessionStatsUpdate] = None


# Live Stats Schemas (Real-time simulcast stats)

class HourlyViewerData(BaseModel):
    """Hourly viewer data point"""
    hour: str
    viewers: int


class ChannelPerformanceData(BaseModel):
    """Channel performance per platform"""
    platform: str
    platform_name: str
    viewers: int


class SocialStatsData(BaseModel):
    """Social engagement stats"""
    views: int = 0
    likes: int = 0
    comments: int = 0


class LiveStatsResponse(BaseModel):
    """Schema for real-time live stats during simulcast"""
    session_id: str
    orders: int = 0
    revenue: float = 0.0
    conversion: float = 0.0
    viewer_count: int = 0
    hourly_viewers: List[HourlyViewerData] = Field(default_factory=list)
    channel_performance: List[ChannelPerformanceData] = Field(default_factory=list)
    social_stats: SocialStatsData = Field(default_factory=SocialStatsData)
