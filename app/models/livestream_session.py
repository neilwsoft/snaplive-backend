"""Livestream Session Models

Database models for livestream session management including session info,
selected products, and stream statistics.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional, Dict, List
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator


def validate_object_id(v: any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class SessionStatus(str, Enum):
    """Livestream session status"""
    PENDING = "pending"      # Session created, not yet started
    LIVE = "live"            # Currently streaming
    ENDED = "ended"          # Stream ended normally
    CANCELLED = "cancelled"  # Session cancelled before going live


class SessionProduct(BaseModel):
    """Product selected for a livestream session"""
    product_id: str = Field(..., description="Product identifier")
    product_name: Dict[str, str] = Field(..., description="Product name in multiple languages")
    sku: str = Field(..., description="Stock Keeping Unit")
    unit_cost: float = Field(..., ge=0, description="Price per unit")
    available_at_start: int = Field(..., ge=0, description="Available stock when session started")
    category: Optional[str] = Field(None, description="Product category")
    image_url: Optional[str] = Field(None, description="Product image URL")

    class Config:
        json_encoders = {ObjectId: str}


class SessionStats(BaseModel):
    """Statistics for a livestream session"""
    peak_viewers: int = Field(default=0, ge=0, description="Maximum concurrent viewers")
    total_viewers: int = Field(default=0, ge=0, description="Total unique viewers")
    products_sold: int = Field(default=0, ge=0, description="Number of products sold during stream")
    revenue: float = Field(default=0.0, ge=0, description="Total revenue from stream")
    message_count: int = Field(default=0, ge=0, description="Total chat messages")
    reaction_count: int = Field(default=0, ge=0, description="Total reactions received")
    average_watch_time_seconds: int = Field(default=0, ge=0, description="Average viewer watch time")


class LivestreamSession(BaseModel):
    """Livestream session model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    seller_id: str = Field(..., description="Seller identifier")
    room_name: str = Field(..., description="LiveKit room name")
    title: Optional[str] = Field(None, description="Stream title")
    description: Optional[str] = Field(None, description="Stream description")
    thumbnail_url: Optional[str] = Field(None, description="Stream thumbnail image URL")
    status: SessionStatus = Field(default=SessionStatus.PENDING)

    # Products selected for this session
    products: List[SessionProduct] = Field(default_factory=list, description="Products for this stream")

    # Broadcast metadata
    platforms: List[str] = Field(default_factory=list, description="Enabled platform names (e.g. Douyin, Taobao Live)")
    category: Optional[str] = Field(None, description="Broadcast category (e.g. Fashion, Beauty)")
    resolution: Optional[str] = Field(None, description="Broadcast resolution (e.g. 1080p, 720p)")

    # Stream configuration
    max_participants: int = Field(default=100, gt=0, description="Maximum viewers allowed")
    enable_agent: bool = Field(default=True, description="Enable AI assistant")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="When stream actually started")
    ended_at: Optional[datetime] = Field(None, description="When stream ended")

    # Statistics (updated during/after stream)
    stats: SessionStats = Field(default_factory=SessionStats)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @property
    def duration_seconds(self) -> int:
        """Calculate stream duration in seconds"""
        if not self.started_at:
            return 0
        end_time = self.ended_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())

    @property
    def product_count(self) -> int:
        """Get number of products in session"""
        return len(self.products)
