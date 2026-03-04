"""Logistics API Schemas

Pydantic schemas for logistics API requests and responses.
"""

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.logistics import ShipmentStatus, Address, PackageDetails


# Carrier Schemas

class CarrierCreate(BaseModel):
    """Schema for creating a carrier"""
    name: Dict[str, str]  # {"en": "...", "ko": "..."}
    code: str
    country: str
    api_endpoint: Optional[str] = None
    supports_tracking: bool = True
    supports_webhooks: bool = False
    is_active: bool = True


class CarrierUpdate(BaseModel):
    """Schema for updating a carrier"""
    name: Optional[Dict[str, str]] = None
    api_endpoint: Optional[str] = None
    supports_tracking: Optional[bool] = None
    supports_webhooks: Optional[bool] = None
    is_active: Optional[bool] = None


class CarrierResponse(BaseModel):
    """Schema for carrier response"""
    id: str = Field(alias="_id")
    name: Dict[str, str]
    code: str
    country: str
    api_endpoint: Optional[str] = None
    supports_tracking: bool
    supports_webhooks: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        # Removed redundant config


# Delivery Zone Schemas

class DeliveryZoneCreate(BaseModel):
    """Schema for creating a delivery zone"""
    name: Dict[str, str]
    carrier_id: str
    origin_country: str
    destination_country: str
    destination_regions: List[str] = []
    base_cost: float
    per_kg_cost: float
    weight_min: float = 0.0
    weight_max: Optional[float] = None
    estimated_days_min: int
    estimated_days_max: int
    is_active: bool = True


class DeliveryZoneUpdate(BaseModel):
    """Schema for updating a delivery zone"""
    name: Optional[Dict[str, str]] = None
    base_cost: Optional[float] = None
    per_kg_cost: Optional[float] = None
    weight_min: Optional[float] = None
    weight_max: Optional[float] = None
    estimated_days_min: Optional[int] = None
    estimated_days_max: Optional[int] = None
    is_active: Optional[bool] = None


class DeliveryZoneResponse(BaseModel):
    """Schema for delivery zone response"""
    id: str = Field(alias="_id")
    name: Dict[str, str]
    carrier_id: str
    carrier_name: Optional[Dict[str, str]] = None
    origin_country: str
    destination_country: str
    destination_regions: List[str]
    base_cost: float
    per_kg_cost: float
    weight_min: float
    weight_max: Optional[float] = None
    estimated_days_min: int
    estimated_days_max: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        # Removed redundant config


class CalculateShippingCostRequest(BaseModel):
    """Schema for shipping cost calculation"""
    carrier_id: Optional[str] = None  # If None, compare all carriers
    origin_country: str
    destination_country: str
    destination_region: Optional[str] = None
    weight: float


class ShippingCostQuote(BaseModel):
    """Schema for shipping cost quote"""
    carrier_id: str
    carrier_name: Dict[str, str]
    delivery_zone_id: str
    cost: float
    currency: str = "USD"
    estimated_days_min: int
    estimated_days_max: int


class CalculateShippingCostResponse(BaseModel):
    """Schema for shipping cost calculation response"""
    quotes: List[ShippingCostQuote]


# Shipment Schemas

class ShipmentCreate(BaseModel):
    """Schema for creating a shipment"""
    order_id: str
    carrier_id: str
    origin: Address
    destination: Address
    package_details: PackageDetails
    warehouse_id: Optional[str] = None
    delivery_zone_id: Optional[str] = None
    tracking_number: Optional[str] = None


class ShipmentUpdate(BaseModel):
    """Schema for updating a shipment"""
    carrier_id: Optional[str] = None
    tracking_number: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    shipping_cost: Optional[float] = None
    qr_code_url: Optional[str] = None
    label_url: Optional[str] = None


class ShipmentResponse(BaseModel):
    """Schema for shipment response"""
    id: str = Field(alias="_id")
    order_id: str
    shipment_number: str
    carrier_id: str
    carrier_name: Optional[Dict[str, str]] = None
    tracking_number: Optional[str] = None
    status: ShipmentStatus
    origin: Address
    destination: Address
    package_details: PackageDetails
    warehouse_id: Optional[str] = None
    delivery_zone_id: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    shipping_cost: Optional[float] = None
    currency: str
    qr_code_url: Optional[str] = None
    label_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    is_delivered: bool
    is_in_transit: bool
    is_pending: bool

    class Config:
        populate_by_name = True
        # Removed redundant config


class ShipmentListResponse(BaseModel):
    """Schema for paginated shipment list"""
    items: List[ShipmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Tracking Event Schemas

class TrackingEventCreate(BaseModel):
    """Schema for creating a tracking event"""
    shipment_id: str
    status: ShipmentStatus
    location: Optional[str] = None
    description: Dict[str, str]  # {"en": "...", "ko": "..."}
    event_time: Optional[datetime] = None


class TrackingEventResponse(BaseModel):
    """Schema for tracking event response"""
    id: str = Field(alias="_id")
    shipment_id: str
    status: ShipmentStatus
    location: Optional[str] = None
    description: Dict[str, str]
    event_time: datetime
    created_at: datetime

    class Config:
        populate_by_name = True
        # Removed redundant config


class TrackingEventListResponse(BaseModel):
    """Schema for tracking event list"""
    items: List[TrackingEventResponse]
    total: int


# QR Code and Label Schemas

class GenerateQRCodeRequest(BaseModel):
    """Schema for QR code generation"""
    shipment_id: str
    size: int = 300  # Size in pixels
    format: str = "png"  # png or svg


class GenerateQRCodeResponse(BaseModel):
    """Schema for QR code generation response"""
    qr_code_url: str
    shipment_id: str


class GenerateLabelRequest(BaseModel):
    """Schema for shipping label generation"""
    shipment_id: str


class GenerateLabelResponse(BaseModel):
    """Schema for shipping label generation response"""
    label_url: str
    shipment_id: str


# Statistics Schema

class LogisticsStatsResponse(BaseModel):
    """Schema for logistics statistics"""
    total_shipments: int
    pending_shipments: int
    in_transit_shipments: int
    delivered_shipments: int
    failed_shipments: int
    total_carriers: int
    active_carriers: int
    total_delivery_zones: int
