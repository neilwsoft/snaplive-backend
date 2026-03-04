from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from app.models.order import OrderStatus, PaymentStatus, Platform, FulfillmentStatus, BadgeType


class ProductBadgeSchema(BaseModel):
    """Schema for product badge"""
    type: str
    label: str


class OrderItemSchema(BaseModel):
    """Schema for order item"""
    product_id: Optional[str] = None
    product_name: Dict[str, str]  # {"ko": "제품명", "zh": "产品名称"}
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    subtotal: float = Field(ge=0)
    sku: Optional[str] = None
    image_url: Optional[str] = None
    unit: str = Field(default="pcs")
    fulfillment_status: Optional[str] = None
    badges: List[ProductBadgeSchema] = Field(default_factory=list)


class ShippingAddressSchema(BaseModel):
    """Schema for shipping address"""
    recipient_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    province: str
    postal_code: str
    country: str


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    buyer_email: EmailStr
    buyer_name: str
    buyer_language: str = Field(default="ko", description="Preferred language: ko or zh")
    buyer_avatar_url: Optional[str] = None
    buyer_phone: Optional[str] = None
    live_simulcast_id: Optional[str] = None
    items: List[OrderItemSchema]
    shipping_address: ShippingAddressSchema
    platform: Platform
    platform_order_id: Optional[str] = None
    buyer_notes: Optional[str] = None
    shipping_fee: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    currency: str = Field(default="CNY")


class OrderUpdate(BaseModel):
    """Schema for updating an order"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    seller_notes: Optional[str] = None
    processing_step: Optional[int] = None
    items: Optional[List[OrderItemSchema]] = None  # For updating fulfillment status

    class Config:
        use_enum_values = True


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: str
    order_number: str
    buyer_email: EmailStr
    buyer_name: str
    buyer_language: str
    buyer_avatar_url: Optional[str] = None
    buyer_phone: Optional[str] = None
    live_simulcast_id: Optional[str] = None
    items: List[OrderItemSchema]
    subtotal: float
    shipping_fee: float
    tax: float
    total: float
    currency: str
    status: OrderStatus
    payment_status: PaymentStatus
    platform: Platform
    platform_order_id: Optional[str]
    shipping_address: ShippingAddressSchema
    tracking_number: Optional[str]
    carrier: Optional[str]
    estimated_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    buyer_notes: Optional[str]
    seller_notes: Optional[str]
    processing_step: int = 1
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema for order list response"""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int
