"""Inventory Models

Database models for inventory management including inventory items,
warehouses, inventory logs, and stock alerts.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional, Dict
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


class InventoryStatus(str, Enum):
    """Inventory item status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class InventoryAction(str, Enum):
    """Types of inventory actions for logging"""
    RESTOCK = "restock"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RESERVATION = "reservation"
    RELEASE = "release"
    RETURN = "return"


class AlertType(str, Enum):
    """Types of stock alerts"""
    LOW_STOCK = "low_stock"
    CRITICAL_STOCK = "critical_stock"
    OVERSTOCK = "overstock"


class ProductCategory(str, Enum):
    """Product categories for inventory items"""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BEAUTY = "beauty"
    FOOD = "food"
    HOME = "home"
    SPORTS = "sports"
    TOYS = "toys"
    OTHER = "other"


class Warehouse(BaseModel):
    """Warehouse model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: Dict[str, str] = Field(..., description="Warehouse name in multiple languages")
    location: str = Field(..., description="Full address or location description")
    city: str
    country: str
    is_default: bool = Field(default=False, description="Default warehouse for new inventory")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Inventory(BaseModel):
    """Inventory item model"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    product_id: str = Field(..., description="Product identifier (can be mock ID)")
    product_name: Dict[str, str] = Field(..., description="Product name in multiple languages")
    warehouse_id: PyObjectId = Field(..., description="Reference to warehouse")
    quantity: int = Field(..., ge=0, description="Total quantity in stock")
    reserved: int = Field(default=0, ge=0, description="Quantity reserved for orders")
    reorder_point: int = Field(..., gt=0, description="Threshold for low stock alert")
    critical_level: int = Field(..., gt=0, description="Threshold for critical stock alert")
    sku: str = Field(..., description="Stock Keeping Unit")
    unit_cost: float = Field(default=0.0, ge=0, description="Cost per unit")
    product_link: Optional[str] = Field(default=None, description="External product URL")
    image_url: Optional[str] = Field(default=None, description="Product image URL")
    category: Optional[ProductCategory] = Field(default=None, description="Product category")
    status: InventoryStatus = Field(default=InventoryStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @property
    def available(self) -> int:
        """Calculate available stock (quantity - reserved)"""
        return max(0, self.quantity - self.reserved)

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is low (below reorder point but above critical)"""
        return self.critical_level < self.available <= self.reorder_point

    @property
    def is_critical_stock(self) -> bool:
        """Check if stock is critical (at or below critical level)"""
        return self.available <= self.critical_level


class InventoryLog(BaseModel):
    """Inventory change log for audit trail"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    inventory_id: PyObjectId = Field(..., description="Reference to inventory item")
    product_name: Dict[str, str] = Field(..., description="Product name for easier querying")
    warehouse_id: PyObjectId = Field(..., description="Reference to warehouse")
    action: InventoryAction = Field(..., description="Type of inventory action")
    quantity_change: int = Field(..., description="Change in quantity (can be negative)")
    previous_quantity: int = Field(..., ge=0)
    new_quantity: int = Field(..., ge=0)
    reference_id: Optional[str] = Field(None, description="Order ID or other reference")
    notes: Optional[str] = Field(None, description="Additional notes about the change")
    created_by: Optional[str] = Field(None, description="User ID who made the change")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class StockAlert(BaseModel):
    """Stock alert for low or critical inventory levels"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    inventory_id: PyObjectId = Field(..., description="Reference to inventory item")
    product_name: Dict[str, str] = Field(..., description="Product name for easier display")
    warehouse_id: PyObjectId = Field(..., description="Reference to warehouse")
    warehouse_name: Dict[str, str] = Field(..., description="Warehouse name")
    sku: str
    alert_type: AlertType
    current_level: int = Field(..., ge=0, description="Current available stock")
    threshold: int = Field(..., description="Threshold that was breached")
    is_acknowledged: bool = Field(default=False)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = Field(None, description="User ID who acknowledged")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
