"""Inventory API Endpoints

API routes for inventory management operations.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.inventory_service import InventoryService
from app.scripts.seed_inventory import seed_inventory_database
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    InventoryListResponse,
    RestockRequest,
    ReserveStockRequest,
    InventoryLogResponse,
    InventoryLogListResponse,
    StockAlertResponse,
    StockAlertListResponse,
    AcknowledgeAlertRequest,
    WarehouseCreate,
    WarehouseResponse,
    InventoryStatsResponse,
    CategoryResponse,
    CategoriesListResponse
)

router = APIRouter()


def get_inventory_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> InventoryService:
    """Dependency to get inventory service"""
    return InventoryService(db)


# Warehouse Endpoints

@router.post("/warehouses", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new warehouse"""
    warehouse = await service.create_warehouse(warehouse_data)
    return WarehouseResponse(
        _id=str(warehouse.id),
        **warehouse.model_dump(exclude={"id"})
    )


@router.get("/warehouses", response_model=List[WarehouseResponse])
async def list_warehouses(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all warehouses"""
    warehouses = await service.list_warehouses()
    return [
        WarehouseResponse(_id=str(w.id), **w.model_dump(exclude={"id"}))
        for w in warehouses
    ]


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get a warehouse by ID"""
    warehouse = await service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    return WarehouseResponse(
        _id=str(warehouse.id),
        **warehouse.model_dump(exclude={"id"})
    )


# Inventory Endpoints

@router.post("/inventory", response_model=InventoryResponse, status_code=201)
async def create_inventory(
    inventory_data: InventoryCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new inventory item"""
    try:
        inventory = await service.create_inventory(inventory_data)

        # Get warehouse for response
        warehouse = await service.get_warehouse(str(inventory.warehouse_id))

        return InventoryResponse(
            _id=str(inventory.id),
            warehouse_id=str(inventory.warehouse_id),
            warehouse_name=warehouse.name if warehouse else None,
            available=inventory.available,
            is_low_stock=inventory.is_low_stock,
            is_critical_stock=inventory.is_critical_stock,
            **inventory.model_dump(exclude={"id", "warehouse_id"})
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory", response_model=InventoryListResponse)
async def list_inventory(
    warehouse_id: Optional[str] = Query(None),
    stock_status: Optional[str] = Query(None, regex="^(all|low|critical|normal)$"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    """List inventory items with filters and pagination"""
    skip = (page - 1) * page_size

    # Handle "all" as None
    if stock_status == "all":
        stock_status = None

    items, total = await service.list_inventory(
        warehouse_id=warehouse_id,
        stock_status=stock_status,
        category=category,
        search=search,
        skip=skip,
        limit=page_size
    )

    # Get warehouse names for responses
    warehouse_map = {}
    if items:
        warehouses = await service.list_warehouses()
        warehouse_map = {str(w.id): w.name for w in warehouses}

    inventory_responses = []
    for item in items:
        inventory_responses.append(
            InventoryResponse(
                _id=str(item.id),
                warehouse_id=str(item.warehouse_id),
                warehouse_name=warehouse_map.get(str(item.warehouse_id)),
                available=item.available,
                is_low_stock=item.is_low_stock,
                is_critical_stock=item.is_critical_stock,
                **item.model_dump(exclude={"id", "warehouse_id"})
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return InventoryListResponse(
        items=inventory_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# Statistics (must come before /{inventory_id} to avoid route conflicts)

@router.get("/inventory/stats", response_model=InventoryStatsResponse)
async def get_inventory_stats(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory statistics"""
    stats = await service.get_inventory_stats()
    return InventoryStatsResponse(**stats)


# Categories (must come before /{inventory_id} to avoid route conflicts)

@router.get("/inventory/categories", response_model=CategoriesListResponse)
async def get_categories(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all product categories with item counts"""
    categories = await service.get_categories()
    return CategoriesListResponse(
        categories=[CategoryResponse(**cat) for cat in categories]
    )


# Inventory Logs (must come before /{inventory_id} to avoid route conflicts)

@router.get("/inventory/logs", response_model=InventoryLogListResponse)
async def get_inventory_logs(
    inventory_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory change logs"""
    skip = (page - 1) * page_size
    logs, total = await service.get_inventory_logs(
        inventory_id=inventory_id,
        skip=skip,
        limit=page_size
    )

    log_responses = [
        InventoryLogResponse(
            _id=str(log.id),
            inventory_id=str(log.inventory_id),
            warehouse_id=str(log.warehouse_id),
            **log.model_dump(exclude={"id", "inventory_id", "warehouse_id"})
        )
        for log in logs
    ]

    return InventoryLogListResponse(
        items=log_responses,
        total=total,
        page=page,
        page_size=page_size
    )


# Stock Alerts (must come before /{inventory_id} to avoid route conflicts)

@router.get("/inventory/alerts", response_model=StockAlertListResponse)
async def get_stock_alerts(
    acknowledged: Optional[bool] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock alerts"""
    alerts = await service.get_stock_alerts(acknowledged=acknowledged)

    alert_responses = [
        StockAlertResponse(
            _id=str(alert.id),
            inventory_id=str(alert.inventory_id),
            warehouse_id=str(alert.warehouse_id),
            **alert.model_dump(exclude={"id", "inventory_id", "warehouse_id"})
        )
        for alert in alerts
    ]

    return StockAlertListResponse(
        items=alert_responses,
        total=len(alert_responses)
    )


@router.post("/inventory/alerts/{alert_id}/acknowledge", response_model=StockAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    ack_data: AcknowledgeAlertRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Acknowledge a stock alert"""
    alert = await service.acknowledge_alert(alert_id, ack_data.acknowledged_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return StockAlertResponse(
        _id=str(alert.id),
        inventory_id=str(alert.inventory_id),
        warehouse_id=str(alert.warehouse_id),
        **alert.model_dump(exclude={"id", "inventory_id", "warehouse_id"})
    )


# Stock Operations (must come before /{inventory_id} to avoid route conflicts)

@router.post("/inventory/restock", response_model=InventoryResponse)
async def restock_inventory(
    restock_data: RestockRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Restock inventory (add quantity)"""
    inventory = await service.restock_inventory(restock_data)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Get warehouse
    warehouse = await service.get_warehouse(str(inventory.warehouse_id))

    return InventoryResponse(
        _id=str(inventory.id),
        warehouse_id=str(inventory.warehouse_id),
        warehouse_name=warehouse.name if warehouse else None,
        available=inventory.available,
        is_low_stock=inventory.is_low_stock,
        is_critical_stock=inventory.is_critical_stock,
        **inventory.model_dump(exclude={"id", "warehouse_id"})
    )


@router.post("/inventory/reserve", response_model=InventoryResponse)
async def reserve_stock(
    reserve_data: ReserveStockRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Reserve stock for an order"""
    try:
        inventory = await service.reserve_stock(reserve_data)
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        # Get warehouse
        warehouse = await service.get_warehouse(str(inventory.warehouse_id))

        return InventoryResponse(
            _id=str(inventory.id),
            warehouse_id=str(inventory.warehouse_id),
            warehouse_name=warehouse.name if warehouse else None,
            available=inventory.available,
            is_low_stock=inventory.is_low_stock,
            is_critical_stock=inventory.is_critical_stock,
            **inventory.model_dump(exclude={"id", "warehouse_id"})
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Parameterized routes (must come after all specific routes to avoid conflicts)

@router.get("/inventory/{inventory_id}", response_model=InventoryResponse)
async def get_inventory(
    inventory_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get an inventory item by ID"""
    inventory = await service.get_inventory(inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Get warehouse
    warehouse = await service.get_warehouse(str(inventory.warehouse_id))

    return InventoryResponse(
        _id=str(inventory.id),
        warehouse_id=str(inventory.warehouse_id),
        warehouse_name=warehouse.name if warehouse else None,
        available=inventory.available,
        is_low_stock=inventory.is_low_stock,
        is_critical_stock=inventory.is_critical_stock,
        **inventory.model_dump(exclude={"id", "warehouse_id"})
    )


@router.put("/inventory/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(
    inventory_id: str,
    update_data: InventoryUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update an inventory item"""
    inventory = await service.update_inventory(inventory_id, update_data)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Get warehouse
    warehouse = await service.get_warehouse(str(inventory.warehouse_id))

    return InventoryResponse(
        _id=str(inventory.id),
        warehouse_id=str(inventory.warehouse_id),
        warehouse_name=warehouse.name if warehouse else None,
        available=inventory.available,
        is_low_stock=inventory.is_low_stock,
        is_critical_stock=inventory.is_critical_stock,
        **inventory.model_dump(exclude={"id", "warehouse_id"})
    )


@router.delete("/inventory/{inventory_id}", status_code=204)
async def delete_inventory(
    inventory_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Delete an inventory item"""
    deleted = await service.delete_inventory(inventory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inventory item not found")


# Database Seeding

@router.post("/seed")
async def seed_database(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Seed the database with dummy inventory data"""
    try:
        await seed_inventory_database(db)
        return {"message": "Inventory database seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
