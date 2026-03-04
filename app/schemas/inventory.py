"""Inventory Schemas

Pydantic schemas for inventory API requests and responses.
"""

from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from app.models.inventory import InventoryStatus, InventoryAction, AlertType, ProductCategory


# Warehouse Schemas

class WarehouseCreate(BaseModel):
    """Schema for creating a warehouse"""
    name: Dict[str, str] = Field(..., description="Warehouse name (en, ko)")
    location: str
    city: str
    country: str
    is_default: bool = False


class WarehouseResponse(BaseModel):
    """Schema for warehouse response"""
    id: str = Field(..., alias="_id")
    name: Dict[str, str]
    location: str
    city: str
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


# Inventory Schemas

class InventoryCreate(BaseModel):
    """Schema for creating inventory item"""
    product_id: str
    product_name: Dict[str, str] = Field(..., description="Product name (en, ko)")
    warehouse_id: str
    quantity: int = Field(..., ge=0)
    reserved: int = Field(default=0, ge=0)
    reorder_point: int = Field(..., gt=0)
    critical_level: int = Field(..., gt=0)
    sku: str
    unit_cost: float = Field(default=0.0, ge=0)
    product_link: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[ProductCategory] = None
    status: InventoryStatus = InventoryStatus.ACTIVE


class InventoryUpdate(BaseModel):
    """Schema for updating inventory item"""
    product_name: Optional[Dict[str, str]] = None
    warehouse_id: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    reserved: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, gt=0)
    critical_level: Optional[int] = Field(None, gt=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    product_link: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[ProductCategory] = None
    status: Optional[InventoryStatus] = None


class RestockRequest(BaseModel):
    """Schema for restocking inventory"""
    inventory_id: str
    quantity: int = Field(..., gt=0, description="Quantity to add")
    notes: Optional[str] = None


class ReserveStockRequest(BaseModel):
    """Schema for reserving stock"""
    inventory_id: str
    quantity: int = Field(..., gt=0)
    reference_id: Optional[str] = Field(None, description="Order ID or reference")


class InventoryResponse(BaseModel):
    """Schema for inventory response"""
    id: str = Field(..., alias="_id")
    product_id: str
    product_name: Dict[str, str]
    warehouse_id: str
    warehouse_name: Optional[Dict[str, str]] = None
    quantity: int
    reserved: int
    available: int
    reorder_point: int
    critical_level: int
    sku: str
    unit_cost: float
    product_link: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[ProductCategory] = None
    status: InventoryStatus
    is_low_stock: bool
    is_critical_stock: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class InventoryListResponse(BaseModel):
    """Schema for paginated inventory list"""
    items: List[InventoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Inventory Log Schemas

class InventoryLogResponse(BaseModel):
    """Schema for inventory log response"""
    id: str = Field(..., alias="_id")
    inventory_id: str
    product_name: Dict[str, str]
    warehouse_id: str
    action: InventoryAction
    quantity_change: int
    previous_quantity: int
    new_quantity: int
    reference_id: Optional[str]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        populate_by_name = True


class InventoryLogListResponse(BaseModel):
    """Schema for paginated inventory log list"""
    items: List[InventoryLogResponse]
    total: int
    page: int
    page_size: int


# Stock Alert Schemas

class StockAlertResponse(BaseModel):
    """Schema for stock alert response"""
    id: str = Field(..., alias="_id")
    inventory_id: str
    product_name: Dict[str, str]
    warehouse_id: str
    warehouse_name: Dict[str, str]
    sku: str
    alert_type: AlertType
    current_level: int
    threshold: int
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: datetime

    class Config:
        populate_by_name = True


class AcknowledgeAlertRequest(BaseModel):
    """Schema for acknowledging an alert"""
    acknowledged_by: Optional[str] = None


class StockAlertListResponse(BaseModel):
    """Schema for stock alert list"""
    items: List[StockAlertResponse]
    total: int


# Statistics Schemas

class InventoryStatsResponse(BaseModel):
    """Schema for inventory statistics"""
    total_items: int
    total_warehouses: int
    low_stock_count: int
    critical_stock_count: int
    total_quantity: int
    total_reserved: int
    total_available: int
    total_value: float


class WarehouseStatsResponse(BaseModel):
    """Schema for warehouse-specific statistics"""
    warehouse_id: str
    warehouse_name: Dict[str, str]
    total_items: int
    total_quantity: int
    total_value: float
    low_stock_items: int
    critical_stock_items: int


class CategoryResponse(BaseModel):
    """Schema for category item"""
    value: str
    label: str
    count: int = 0


class CategoriesListResponse(BaseModel):
    """Schema for categories list response"""
    categories: List[CategoryResponse]
