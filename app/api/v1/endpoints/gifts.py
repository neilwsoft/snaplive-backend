"""Gift API Endpoints

API routes for virtual gift management operations.
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.gift_service import GiftService
from app.schemas.gift import (
    GiftCreate,
    GiftUpdate,
    GiftResponse,
    GiftListResponse,
)

router = APIRouter()


def get_gift_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> GiftService:
    """Dependency to get gift service"""
    return GiftService(db)


def _gift_to_response(gift) -> dict:
    """Convert Gift model to response dict"""
    return {
        "_id": str(gift.id),
        "raw_gift_name": gift.raw_gift_name,
        "image_url": gift.image_url,
        "quantity": gift.quantity,
        "marketplace_source": gift.marketplace_source,
        "live_simulcast_id": gift.live_simulcast_id,
        "viewer_username": gift.viewer_username,
        "viewer_avatar_url": gift.viewer_avatar_url,
        "gifting_timestamp": gift.gifting_timestamp,
        "virtual_currency_value": gift.virtual_currency_value,
        "currency_label": gift.currency_label,
        "tier_level": gift.tier_level,
        "seller_id": gift.seller_id,
        "created_at": gift.created_at,
        "updated_at": gift.updated_at,
    }


@router.post("/", response_model=GiftResponse, status_code=201)
async def create_gift(
    gift_data: GiftCreate,
    service: GiftService = Depends(get_gift_service),
):
    """Create a new gift record"""
    gift = await service.create_gift(gift_data)
    return _gift_to_response(gift)


@router.get("/", response_model=GiftListResponse)
async def list_gifts(
    marketplace_source: Optional[str] = Query(None, description="Filter by marketplace source"),
    tier_level: Optional[str] = Query(None, description="Filter by tier level"),
    live_simulcast_id: Optional[str] = Query(None, description="Filter by simulcast ID"),
    search: Optional[str] = Query(None, description="Search by gift name, viewer, or simulcast ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    service: GiftService = Depends(get_gift_service),
):
    """List gifts with filtering and pagination"""
    items, total = await service.get_gifts(
        marketplace_source=marketplace_source,
        tier_level=tier_level,
        live_simulcast_id=live_simulcast_id,
        search=search,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "items": [_gift_to_response(g) for g in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/stats")
async def get_gift_stats(
    service: GiftService = Depends(get_gift_service),
):
    """Get gift statistics"""
    return await service.get_gift_stats()


@router.post("/seed")
async def seed_gifts(
    count: int = Query(24, ge=1, le=200, description="Number of gifts to seed"),
    service: GiftService = Depends(get_gift_service),
):
    """Seed database with sample gift data"""
    gifts = await service.seed_gifts(count=count)
    return {
        "message": f"Successfully seeded {len(gifts)} gifts",
        "count": len(gifts),
    }


@router.get("/{gift_id}", response_model=GiftResponse)
async def get_gift(
    gift_id: str,
    service: GiftService = Depends(get_gift_service),
):
    """Get a single gift by ID"""
    gift = await service.get_gift(gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return _gift_to_response(gift)


@router.patch("/{gift_id}", response_model=GiftResponse)
async def update_gift(
    gift_id: str,
    update_data: GiftUpdate,
    service: GiftService = Depends(get_gift_service),
):
    """Update a gift"""
    gift = await service.update_gift(gift_id, update_data)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return _gift_to_response(gift)


@router.delete("/{gift_id}")
async def delete_gift(
    gift_id: str,
    service: GiftService = Depends(get_gift_service),
):
    """Delete a gift"""
    deleted = await service.delete_gift(gift_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Gift not found")
    return {"message": "Gift deleted successfully"}
