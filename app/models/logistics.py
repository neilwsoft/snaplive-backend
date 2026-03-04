"""Logistics Database Models

Pydantic models for logistics management including shipments, carriers,
delivery zones, and tracking events.
"""

from typing import Optional, List, Dict, Annotated
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class ShipmentStatus(str, Enum):
    """Shipment status enumeration"""
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class Address(BaseModel):
    """Address model for origin and destination"""
    name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: str
    country: str

    class Config:
        populate_by_name = True


class PackageDetails(BaseModel):
    """Package dimensions and weight"""
    weight: float  # in kg
    length: Optional[float] = None  # in cm
    width: Optional[float] = None  # in cm
    height: Optional[float] = None  # in cm
    declared_value: Optional[float] = None

    class Config:
        populate_by_name = True


class Carrier(BaseModel):
    """Carrier/Courier model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: Dict[str, str]  # {"en": "...", "ko": "..."}
    code: str  # Unique carrier code (e.g., "taobao", "sf-express", "cj-logistics")
    country: str
    api_endpoint: Optional[str] = None
    supports_tracking: bool = True
    supports_webhooks: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DeliveryZone(BaseModel):
    """Delivery zone with pricing rules"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: Dict[str, str]  # {"en": "...", "ko": "..."}
    carrier_id: PyObjectId
    origin_country: str
    destination_country: str
    destination_regions: List[str] = []  # Provinces/states
    base_cost: float  # Base shipping cost
    per_kg_cost: float  # Cost per kilogram
    weight_min: float = 0.0  # Minimum weight in kg
    weight_max: Optional[float] = None  # Maximum weight in kg
    estimated_days_min: int  # Minimum delivery days
    estimated_days_max: int  # Maximum delivery days
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    def calculate_cost(self, weight: float) -> float:
        """Calculate shipping cost for given weight"""
        if self.weight_max and weight > self.weight_max:
            raise ValueError(f"Weight {weight}kg exceeds maximum {self.weight_max}kg")
        if weight < self.weight_min:
            raise ValueError(f"Weight {weight}kg below minimum {self.weight_min}kg")

        return self.base_cost + (weight * self.per_kg_cost)


class Shipment(BaseModel):
    """Shipment model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    order_id: PyObjectId
    shipment_number: str  # Unique shipment identifier
    carrier_id: PyObjectId
    tracking_number: Optional[str] = None
    status: ShipmentStatus = ShipmentStatus.PENDING

    # Origin and destination
    origin: Address
    destination: Address

    # Package information
    package_details: PackageDetails

    # Delivery information
    warehouse_id: Optional[PyObjectId] = None
    delivery_zone_id: Optional[PyObjectId] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None

    # Costs
    shipping_cost: Optional[float] = None
    currency: str = "USD"

    # Documents
    qr_code_url: Optional[str] = None
    label_url: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @property
    def is_delivered(self) -> bool:
        """Check if shipment is delivered"""
        return self.status == ShipmentStatus.DELIVERED

    @property
    def is_in_transit(self) -> bool:
        """Check if shipment is in transit"""
        return self.status in [
            ShipmentStatus.PICKED_UP,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.OUT_FOR_DELIVERY
        ]

    @property
    def is_pending(self) -> bool:
        """Check if shipment is pending"""
        return self.status == ShipmentStatus.PENDING


class TrackingEvent(BaseModel):
    """Tracking event for shipment updates"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    shipment_id: PyObjectId
    status: ShipmentStatus
    location: Optional[str] = None
    description: Dict[str, str]  # {"en": "...", "ko": "..."}
    event_time: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
