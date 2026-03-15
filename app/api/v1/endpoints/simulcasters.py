"""Simulcaster API Endpoints

API routes for simulcaster operations including top simulcasters leaderboard.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.simulcaster_service import SimulcasterService
from app.schemas.simulcaster import (
    TopSimulcastersListResponse,
    TopSimulcasterResponse,
    SellerProfileResponse,
)

router = APIRouter()


def get_simulcaster_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SimulcasterService:
    """Dependency to get simulcaster service"""
    return SimulcasterService(db)


@router.get("/top", response_model=TopSimulcastersListResponse)
async def get_top_simulcasters(
    time_period: Optional[str] = Query(
        "all_time",
        description="Time period filter: all_time, month, or week"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace/platform"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    service: SimulcasterService = Depends(get_simulcaster_service),
):
    """
    Get top simulcasters ranked by performance metrics

    Returns a leaderboard of simulcasters sorted by total views,
    with aggregated stats from their livestream sessions.
    """
    skip = (page - 1) * page_size

    items, total = await service.get_top_simulcasters(
        time_period=time_period,
        category=category,
        marketplace=marketplace,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return TopSimulcastersListResponse(
        items=[TopSimulcasterResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{seller_id}", response_model=SellerProfileResponse)
async def get_seller_profile(
    seller_id: str,
    service: SimulcasterService = Depends(get_simulcaster_service),
):
    """
    Get a seller's profile with aggregated stats and recent session history.
    """
    profile = await service.get_seller_profile(seller_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Seller not found")
    return SellerProfileResponse(**profile)
