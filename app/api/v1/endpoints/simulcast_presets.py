"""Simulcast Preset API Endpoints

API routes for simulcast preset management operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.simulcast_preset_service import SimulcastPresetService
from app.schemas.simulcast_preset import (
    SimulcastPresetCreate,
    SimulcastPresetUpdate,
    SimulcastPresetResponse,
    SimulcastPresetListResponse,
    PlatformConfigResponse,
    PresetProductResponse,
    CameraConfigResponse,
    BrandingConfigResponse,
)

router = APIRouter()


def get_preset_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SimulcastPresetService:
    """Dependency to get simulcast preset service"""
    return SimulcastPresetService(db)


def _preset_to_response(preset) -> SimulcastPresetResponse:
    """Convert preset model to response"""
    return SimulcastPresetResponse(
        _id=str(preset.id),
        seller_id=preset.seller_id,
        title=preset.title,
        description=preset.description,
        resolution=preset.resolution,
        platforms=[PlatformConfigResponse(**p.model_dump()) for p in preset.platforms],
        products=[PresetProductResponse(**p.model_dump()) for p in preset.products],
        product_count=preset.product_count,
        invited_user_ids=preset.invited_user_ids,
        cameras=[CameraConfigResponse(**c.model_dump()) for c in preset.cameras],
        branding=BrandingConfigResponse(**preset.branding.model_dump()),
        created_at=preset.created_at,
        updated_at=preset.updated_at,
        last_used_at=preset.last_used_at,
        use_count=preset.use_count,
    )


# CRUD Endpoints


@router.post("", response_model=SimulcastPresetResponse, status_code=201)
async def create_preset(
    preset_data: SimulcastPresetCreate,
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """Create a new simulcast preset"""
    preset = await service.create_preset(preset_data)
    return _preset_to_response(preset)


@router.get("", response_model=SimulcastPresetListResponse)
async def list_presets(
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """List simulcast presets with filters and pagination"""
    skip = (page - 1) * page_size

    items, total = await service.list_presets(
        seller_id=seller_id,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return SimulcastPresetListResponse(
        items=[_preset_to_response(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{preset_id}", response_model=SimulcastPresetResponse)
async def get_preset(
    preset_id: str,
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """Get a simulcast preset by ID"""
    preset = await service.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return _preset_to_response(preset)


@router.patch("/{preset_id}", response_model=SimulcastPresetResponse)
async def update_preset(
    preset_id: str,
    update_data: SimulcastPresetUpdate,
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """Update a simulcast preset"""
    preset = await service.update_preset(preset_id, update_data)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return _preset_to_response(preset)


@router.delete("/{preset_id}", status_code=204)
async def delete_preset(
    preset_id: str,
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """Delete a simulcast preset"""
    deleted = await service.delete_preset(preset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Preset not found")


# Usage Tracking Endpoint


@router.post("/{preset_id}/use", response_model=SimulcastPresetResponse)
async def mark_preset_used(
    preset_id: str,
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """Mark a preset as used (increments use count and updates last_used_at)"""
    preset = await service.increment_use_count(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return _preset_to_response(preset)


# Seed Endpoint (Development only)


@router.post("/seed", response_model=list[SimulcastPresetResponse])
async def seed_dummy_presets(
    seller_id: str = Query(..., description="Seller ID to create presets for"),
    count: int = Query(5, ge=1, le=20, description="Number of presets to create"),
    service: SimulcastPresetService = Depends(get_preset_service),
):
    """Seed dummy presets for testing (development only)"""
    presets = await service.seed_dummy_presets(seller_id, count)
    return [_preset_to_response(p) for p in presets]
