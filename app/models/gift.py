"""Gift Models

Database models for virtual gift management in livestream sessions.
Tracks gifts sent by viewers across multiple marketplace platforms.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator


def validate_object_id(v) -> ObjectId:
    """Validate and convert to ObjectId"""
    if v is None:
        return v
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(str(v)):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class MarketplaceSource(str, Enum):
    """Marketplace platform where gift was sent"""
    DOUYIN = "douyin"
    TAOBAO = "taobao"
    XIAOHONGSHU = "xiaohongshu"
    SNAPLIVE = "snaplive"


class TierLevel(str, Enum):
    """Gift tier level classification"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    PREMIUM = "premium"


class Gift(BaseModel):
    """Virtual gift model for MongoDB"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    raw_gift_name: str = Field(..., description="Original gift name with Chinese characters")
    image_url: Optional[str] = Field(None, description="Gift image/thumbnail URL")
    quantity: int = Field(default=1, ge=1, description="Number of gifts sent")
    marketplace_source: MarketplaceSource = Field(..., description="Platform where gift was sent")
    live_simulcast_id: str = Field(..., description="Live simulcast session identifier")
    viewer_username: str = Field(..., description="Username of the viewer who sent the gift")
    viewer_avatar_url: Optional[str] = Field(None, description="Viewer avatar image URL")
    gifting_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the gift was sent")
    virtual_currency_value: float = Field(default=0.0, ge=0, description="Value in platform virtual currency")
    currency_label: Optional[str] = Field(None, description="Platform currency name (e.g., Douyin coins)")
    tier_level: TierLevel = Field(default=TierLevel.LARGE, description="Gift tier classification")
    seller_id: Optional[str] = Field(None, description="Associated seller identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
