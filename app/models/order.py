from datetime import datetime
from typing import Optional, List, Dict, Annotated
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if v is None:
        return v
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(str(v)):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Pydantic v2 compatible ObjectId type
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class OrderStatus(str, Enum):
    """Order status enum - matches frontend statuses"""
    PENDING = "pending"
    READY = "ready"  # Ready for shipping
    SHOPPING = "shopping"  # Being processed/shopped
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNING = "returning"  # Return in progress
    RETURN = "return"  # Returned


class PaymentStatus(str, Enum):
    """Payment status enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Platform(str, Enum):
    """E-commerce platform enum"""
    TAOBAO = "taobao"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    SNAPLIVE = "snaplive"
    DIRECT = "direct"


class FulfillmentStatus(str, Enum):
    """Fulfillment status for order items"""
    PICK = "pick"
    PACK = "pack"
    SHIP = "ship"


class BadgeType(str, Enum):
    """Product badge types"""
    NEW = "new"
    BESTSELLER = "bestseller"
    HOT_SELLER = "hot-seller"


class ProductBadge(BaseModel):
    """Product badge model"""
    type: BadgeType
    label: str


class OrderItem(BaseModel):
    """Order item model"""
    product_id: Optional[str] = None  # Product ID as string (not ObjectId)
    product_name: Dict[str, str]  # {"ko": "제품명", "zh": "产品名称"}
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    subtotal: float = Field(ge=0)
    sku: Optional[str] = None
    image_url: Optional[str] = None
    unit: str = Field(default="pcs")  # e.g., 'pcs', 'unit'
    fulfillment_status: Optional[FulfillmentStatus] = None
    badges: List[ProductBadge] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ShippingAddress(BaseModel):
    """Shipping address model"""
    recipient_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    province: str
    postal_code: str
    country: str


class Order(BaseModel):
    """Order model for MongoDB"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    order_number: str = Field(..., description="Unique order number")

    # Buyer information
    buyer_id: Optional[PyObjectId] = None
    buyer_email: EmailStr
    buyer_name: str
    buyer_language: str = Field(default="ko", description="Preferred language: ko or zh")
    buyer_avatar_url: Optional[str] = None
    buyer_phone: Optional[str] = None

    # Live simulcast reference
    live_simulcast_id: Optional[str] = None

    # Order items
    items: List[OrderItem] = Field(default_factory=list)

    # Pricing
    subtotal: float = Field(ge=0)
    shipping_fee: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    total: float = Field(ge=0)
    currency: str = Field(default="CNY")

    # Status
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)

    # Platform
    platform: Platform
    platform_order_id: Optional[str] = None  # Original platform order ID

    # Shipping
    shipping_address: ShippingAddress
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None

    # Seller
    seller_id: Optional[PyObjectId] = None

    # Notes
    buyer_notes: Optional[str] = None
    seller_notes: Optional[str] = None

    # Processing step (1 = select products, 2 = shipping form)
    processing_step: int = Field(default=1)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True
        use_enum_values = True
