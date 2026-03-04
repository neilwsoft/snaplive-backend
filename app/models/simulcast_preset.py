"""Simulcast Preset Models

Database models for storing simulcast preset configurations
including platforms, products, cameras, and branding settings.
"""

from datetime import datetime
from typing import Annotated, Optional, List
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


class PlatformConfig(BaseModel):
    """Platform configuration for simulcast"""
    name: str = Field(..., description="Platform name (Douyin, Xiaohongshu, Taobao Live)")
    connected: bool = Field(default=False, description="Connection status")
    signal_strength: int = Field(default=0, ge=0, le=5, description="Signal strength 0-5")


class PresetProduct(BaseModel):
    """Product selected for a preset"""
    product_id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product display name")
    image_url: Optional[str] = Field(None, description="Product image URL")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    quantity: Optional[int] = Field(None, ge=0, description="Available quantity")
    unit_cost: Optional[float] = Field(None, ge=0, description="Price per unit")
    category: Optional[str] = Field(None, description="Product category")


class CameraConfig(BaseModel):
    """Camera configuration"""
    camera_id: str = Field(..., description="Camera device ID")
    name: str = Field(..., description="Camera display name")
    selected: bool = Field(default=True, description="Whether camera is selected")
    preview_url: Optional[str] = Field(None, description="Camera preview URL")


class BrandingConfig(BaseModel):
    """Branding configuration"""
    landscape_logo_url: Optional[str] = Field(None, description="Landscape logo URL (340x112px)")
    boxed_logo_url: Optional[str] = Field(None, description="Boxed/square logo URL (112x112px)")


class SimulcastPreset(BaseModel):
    """Simulcast preset model - stores full configuration for reuse"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    seller_id: str = Field(..., description="Seller identifier")

    # Basic info
    title: str = Field(..., description="Preset/stream title")
    description: Optional[str] = Field(None, description="Preset description")
    resolution: str = Field(default="Auto", description="Resolution setting (Auto, 4K, 1080p, 720p, 480p)")

    # Platform configuration
    platforms: List[PlatformConfig] = Field(default_factory=list)

    # Selected products
    products: List[PresetProduct] = Field(default_factory=list)

    # Invited users
    invited_user_ids: List[str] = Field(default_factory=list)

    # Camera settings
    cameras: List[CameraConfig] = Field(default_factory=list)

    # Branding
    branding: BrandingConfig = Field(default_factory=BrandingConfig)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Usage tracking
    last_used_at: Optional[datetime] = Field(None, description="When preset was last used")
    use_count: int = Field(default=0, ge=0, description="Number of times preset was used")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @property
    def product_count(self) -> int:
        """Get number of products in preset"""
        return len(self.products)
