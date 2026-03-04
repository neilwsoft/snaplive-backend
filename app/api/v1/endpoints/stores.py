"""Store Connection API Endpoints

Endpoints for managing marketplace store connections, synchronization, and dashboards.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.database import get_database
from app.services.platform_service import PlatformService
from app.services.sync_service import SyncService
from app.schemas.store import (
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    StoreListResponse,
    StoreDashboardMetrics,
    StoreConnectionTest,
)
from app.schemas.sync import (
    SyncTrigger,
    SyncResponse,
    SyncListResponse,
    SyncStatusResponse,
)
from app.models.platform_store import Platform
from app.models.sync_log import SyncType

router = APIRouter()


@router.post("/stores", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_store_connection(
    store_data: StoreCreate,
    seller_id: str = Query(..., description="Seller ID"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a new platform store connection.
    """
    service = PlatformService(db)

    # Extract credentials from request
    credentials = {
        "api_key": store_data.api_key,
        "api_secret": store_data.api_secret,
        "app_key": store_data.app_key,
        "session_key": store_data.session_key,
        "client_key": store_data.client_key,
        "client_secret": store_data.client_secret,
        "app_id": store_data.app_id,
        "app_secret": store_data.app_secret,
        "access_token": store_data.access_token,
        "refresh_token": store_data.refresh_token,
    }
    credentials = {k: v for k, v in credentials.items() if v}  # Remove None values

    result = await service.create_store_connection(
        seller_id=seller_id,
        platform=store_data.platform,
        store_id=store_data.store_id,
        store_name=store_data.store_name,
        credentials=credentials,
        store_url=store_data.store_url,
        config=store_data.config,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


@router.get("/stores", response_model=StoreListResponse)
async def list_stores(
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    platform: Optional[Platform] = Query(None, description="Filter by platform"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List all store connections with optional filters.
    """
    service = PlatformService(db)
    result = await service.list_stores(
        seller_id=seller_id,
        platform=platform,
        page=page,
        page_size=page_size,
    )

    return result


@router.get("/stores/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get a specific store connection by ID.
    """
    service = PlatformService(db)
    store = await service.get_store(store_id)

    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )

    return store


@router.put("/stores/{store_id}", response_model=dict)
async def update_store(
    store_id: str,
    updates: StoreUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update a store connection.
    """
    service = PlatformService(db)

    # Build updates dict from provided fields
    update_dict = {}
    if updates.store_name is not None:
        update_dict["store_name"] = updates.store_name
    if updates.store_url is not None:
        update_dict["store_url"] = updates.store_url
    if updates.connection_status is not None:
        update_dict["connection_status"] = updates.connection_status.value
    if updates.config is not None:
        update_dict["config"] = updates.config.dict()

    result = await service.update_store(store_id, update_dict)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"],
        )

    return result


@router.delete("/stores/{store_id}", response_model=dict)
async def delete_store(
    store_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Delete a store connection.
    """
    service = PlatformService(db)
    result = await service.delete_store(store_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"],
        )

    return result


@router.post("/stores/{store_id}/test", response_model=StoreConnectionTest)
async def test_store_connection(
    store_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Test the connection to a store's platform.
    """
    service = PlatformService(db)
    result = await service.test_store_connection(store_id)

    return result


@router.post("/stores/{store_id}/sync", response_model=dict)
async def trigger_store_sync(
    store_id: str,
    sync_data: SyncTrigger,
    user_id: Optional[str] = Query(None, description="User triggering the sync"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Trigger a synchronization operation for a store.
    """
    sync_service = SyncService(db)

    result = await sync_service.trigger_sync(
        store_id=store_id,
        sync_type=sync_data.sync_type,
        sync_direction=sync_data.sync_direction,
        triggered_by="manual",
        user_id=user_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


@router.get("/stores/{store_id}/sync-status", response_model=SyncStatusResponse)
async def get_store_sync_status(
    store_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get current synchronization status for a store.
    """
    sync_service = SyncService(db)
    status_data = await sync_service.get_sync_status(store_id)

    if "error" in status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=status_data["error"],
        )

    return status_data


@router.get("/stores/{store_id}/sync-history", response_model=SyncListResponse)
async def get_store_sync_history(
    store_id: str,
    sync_type: Optional[SyncType] = Query(None, description="Filter by sync type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get synchronization history for a store.
    """
    sync_service = SyncService(db)
    history = await sync_service.get_sync_history(
        store_id=store_id,
        sync_type=sync_type,
        page=page,
        page_size=page_size,
    )

    return history


@router.get("/stores/{store_id}/dashboard", response_model=StoreDashboardMetrics)
async def get_store_dashboard(
    store_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get dashboard metrics for a specific store.
    This endpoint returns comprehensive metrics including:
    - Connection health
    - Sales metrics
    - Inventory status
    - Live streaming metrics
    """
    platform_service = PlatformService(db)
    sync_service = SyncService(db)

    # Get store
    store = await platform_service.get_store(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )

    # Get sync status
    sync_status = await sync_service.get_sync_status(store_id)

    # Mock dashboard metrics (in production, fetch from actual data)
    from datetime import datetime
    import random

    metrics = {
        "store_id": store_id,
        "platform": store["platform"],
        "store_name": store["store_name"],
        # Connection health
        "connection_status": store["connection_status"],
        "last_sync_at": store.get("last_sync_at"),
        "last_sync_error": store.get("last_sync_error"),
        "api_calls_remaining": random.randint(1000, 5000),
        "rate_limit_reset_at": datetime.utcnow(),
        # Sales metrics (mock data)
        "orders_today": random.randint(10, 100),
        "orders_this_week": random.randint(50, 500),
        "orders_this_month": random.randint(200, 2000),
        "revenue_today": round(random.uniform(1000, 10000), 2),
        "revenue_this_week": round(random.uniform(5000, 50000), 2),
        "revenue_this_month": round(random.uniform(20000, 200000), 2),
        "average_order_value": round(random.uniform(50, 500), 2),
        "conversion_rate": round(random.uniform(2, 15), 2),
        # Inventory status (mock data)
        "total_products": random.randint(50, 500),
        "in_stock_products": random.randint(40, 450),
        "out_of_stock_products": random.randint(0, 50),
        "low_stock_products": random.randint(5, 30),
        "sync_conflicts": random.randint(0, 5),
        # Live streaming metrics (mock data)
        "active_streams": random.randint(0, 3),
        "total_viewers_today": random.randint(1000, 50000),
        "peak_concurrent_viewers": random.randint(500, 10000),
        "average_watch_time_minutes": round(random.uniform(10, 60), 1),
        "engagement_rate": round(random.uniform(15, 60), 1),
        "products_shown_in_stream": random.randint(5, 30),
        # Sync health
        "sync_success_rate_24h": sync_status.get("success_rate_today", 0),
        "pending_sync_items": random.randint(0, 20),
    }

    return metrics
