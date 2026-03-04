"""Gift Schemas

Pydantic schemas for gift API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class GiftCreate(BaseModel):
    """Schema for creating a new gift"""
    raw_gift_name: str = Field(..., description="Original gift name")
    image_url: Optional[str] = Field(None, description="Gift image URL")
    quantity: int = Field(default=1, ge=1, description="Number of gifts")
    marketplace_source: str = Field(..., description="Platform source")
    live_simulcast_id: str = Field(..., description="Live simulcast ID")
    viewer_username: str = Field(..., description="Viewer username")
    viewer_avatar_url: Optional[str] = Field(None, description="Viewer avatar URL")
    gifting_timestamp: Optional[datetime] = Field(None, description="Gift timestamp")
    virtual_currency_value: float = Field(default=0.0, ge=0, description="Currency value")
    currency_label: Optional[str] = Field(None, description="Currency name")
    tier_level: str = Field(default="large", description="Gift tier level")
    seller_id: Optional[str] = Field(None, description="Seller ID")


class GiftUpdate(BaseModel):
    """Schema for updating a gift"""
    raw_gift_name: Optional[str] = None
    image_url: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    marketplace_source: Optional[str] = None
    live_simulcast_id: Optional[str] = None
    viewer_username: Optional[str] = None
    viewer_avatar_url: Optional[str] = None
    gifting_timestamp: Optional[datetime] = None
    virtual_currency_value: Optional[float] = Field(None, ge=0)
    currency_label: Optional[str] = None
    tier_level: Optional[str] = None
    seller_id: Optional[str] = None


class GiftResponse(BaseModel):
    """Schema for gift API response"""
    id: str = Field(..., alias="_id")
    raw_gift_name: str
    image_url: Optional[str] = None
    quantity: int
    marketplace_source: str
    live_simulcast_id: str
    viewer_username: str
    viewer_avatar_url: Optional[str] = None
    gifting_timestamp: datetime
    virtual_currency_value: float
    currency_label: Optional[str] = None
    tier_level: str
    seller_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class GiftListResponse(BaseModel):
    """Schema for paginated gift list response"""
    items: List[GiftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
