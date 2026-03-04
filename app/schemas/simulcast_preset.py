"""Simulcast Preset Schemas

Request and response schemas for simulcast preset API endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Nested schemas for platform config
class PlatformConfigCreate(BaseModel):
    """Platform configuration for create/update requests"""
    name: str = Field(..., description="Platform name")
    connected: bool = Field(default=False)
    signal_strength: int = Field(default=0, ge=0, le=5)


# Nested schemas for products
class PresetProductCreate(BaseModel):
    """Product data for create/update requests"""
    product_id: str
    name: str
    image_url: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[int] = None
    unit_cost: Optional[float] = None
    category: Optional[str] = None


# Nested schemas for cameras
class CameraConfigCreate(BaseModel):
    """Camera configuration for create/update requests"""
    camera_id: str
    name: str
    selected: bool = True
    preview_url: Optional[str] = None


# Nested schemas for branding
class BrandingConfigCreate(BaseModel):
    """Branding configuration for create/update requests"""
    landscape_logo_url: Optional[str] = None
    boxed_logo_url: Optional[str] = None


# Main request schemas
class SimulcastPresetCreate(BaseModel):
    """Schema for creating a new simulcast preset"""
    seller_id: str = Field(..., description="Seller identifier")
    title: str = Field(..., description="Preset title")
    description: Optional[str] = Field(None, description="Preset description")
    resolution: str = Field(default="Auto", description="Resolution setting")
    platforms: List[PlatformConfigCreate] = Field(default_factory=list)
    products: List[PresetProductCreate] = Field(default_factory=list)
    invited_user_ids: List[str] = Field(default_factory=list)
    cameras: List[CameraConfigCreate] = Field(default_factory=list)
    branding: BrandingConfigCreate = Field(default_factory=BrandingConfigCreate)


class SimulcastPresetUpdate(BaseModel):
    """Schema for updating an existing simulcast preset"""
    title: Optional[str] = None
    description: Optional[str] = None
    resolution: Optional[str] = None
    platforms: Optional[List[PlatformConfigCreate]] = None
    products: Optional[List[PresetProductCreate]] = None
    invited_user_ids: Optional[List[str]] = None
    cameras: Optional[List[CameraConfigCreate]] = None
    branding: Optional[BrandingConfigCreate] = None


# Response schemas
class PlatformConfigResponse(BaseModel):
    """Platform configuration in response"""
    name: str
    connected: bool
    signal_strength: int


class PresetProductResponse(BaseModel):
    """Product data in response"""
    product_id: str
    name: str
    image_url: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[int] = None
    unit_cost: Optional[float] = None
    category: Optional[str] = None


class CameraConfigResponse(BaseModel):
    """Camera configuration in response"""
    camera_id: str
    name: str
    selected: bool
    preview_url: Optional[str] = None


class BrandingConfigResponse(BaseModel):
    """Branding configuration in response"""
    landscape_logo_url: Optional[str] = None
    boxed_logo_url: Optional[str] = None


class SimulcastPresetResponse(BaseModel):
    """Response schema for a single simulcast preset"""
    id: str = Field(..., alias="_id")
    seller_id: str
    title: str
    description: Optional[str] = None
    resolution: str
    platforms: List[PlatformConfigResponse]
    products: List[PresetProductResponse]
    product_count: int
    invited_user_ids: List[str]
    cameras: List[CameraConfigResponse]
    branding: BrandingConfigResponse
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    use_count: int

    class Config:
        populate_by_name = True


class SimulcastPresetListResponse(BaseModel):
    """Response schema for paginated list of presets"""
    items: List[SimulcastPresetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
