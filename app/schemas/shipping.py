"""
Shipping Schemas

Pydantic schemas for shipping address API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SavedAddressBase(BaseModel):
    """Base schema for saved addresses"""
    label: Optional[str] = None
    name: str = Field(..., description="Contact name")
    contact_number: str = Field(..., description="Phone number")
    email: Optional[str] = None
    address_line1: str = Field(..., description="Street address")
    address_line2: Optional[str] = None
    city: str
    province: str
    postal_code: str
    country: str = Field(default="China")
    is_default: bool = Field(default=False)


class SavedAddressCreate(SavedAddressBase):
    """Schema for creating a saved address"""
    pass


class SavedAddressUpdate(BaseModel):
    """Schema for updating a saved address"""
    label: Optional[str] = None
    name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None


class SavedAddressResponse(SavedAddressBase):
    """Schema for saved address response"""
    id: str = Field(..., alias="_id")
    address_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class SavedAddressListResponse(BaseModel):
    """Schema for list of saved addresses"""
    items: List[SavedAddressResponse]
    total: int


# Logistics Provider Schemas

class LogisticsProviderBase(BaseModel):
    """Base schema for logistics provider"""
    code: str
    name: str
    name_zh: str
    service_types: List[str] = Field(default_factory=lambda: ["standard", "express", "economy"])
    is_active: bool = True


class LogisticsProviderResponse(LogisticsProviderBase):
    """Schema for logistics provider response"""
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class LogisticsProviderListResponse(BaseModel):
    """Schema for list of logistics providers"""
    providers: List[LogisticsProviderResponse]


# Order Processing Schemas

class GoodsDetailsSchema(BaseModel):
    """Schema for goods details in order processing"""
    products: List[dict]  # List of {name, description}
    total_quantity: int
    total_declared_value: float
    currency: str = "CNY"
    gross_weight: float = Field(ge=0)
    number_of_packages: int = Field(ge=1)


class ShipperInfoSchema(BaseModel):
    """Schema for shipper (consignor) info"""
    name: str
    contact_number: str
    email: Optional[str] = None
    dispatch_address: str


class RecipientInfoSchema(BaseModel):
    """Schema for recipient (consignee) info"""
    name: str
    contact_number: str
    email: Optional[str] = None
    dispatch_address: str


class WaybillInfoSchema(BaseModel):
    """Schema for e-waybill info"""
    logistics_provider: str
    live_hub_order_id: Optional[str] = None
    marketplace_order_id: str
    marketplace: str
    shipping_service_type: str = "standard"


class LogisticsNotesSchema(BaseModel):
    """Schema for payment and logistics notes"""
    payment_method: str = "seller-pays"  # "seller-pays" | "buyer-pays"
    delivery_instructions: Optional[str] = None
    remarks_insurance: Optional[str] = None


class OrderProcessingRequest(BaseModel):
    """Schema for order processing request (step 2)"""
    goods_details: GoodsDetailsSchema
    shipper: ShipperInfoSchema
    recipient: RecipientInfoSchema
    waybill: WaybillInfoSchema
    notes: Optional[LogisticsNotesSchema] = None


class OrderProcessingResponse(BaseModel):
    """Schema for order processing response"""
    success: bool
    order_id: str
    tracking_number: Optional[str] = None
    carrier: str
    status: str
    message: str
