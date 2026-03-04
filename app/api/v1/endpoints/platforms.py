"""Platform API Endpoints

Endpoints for managing platform connections and information.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.platform_service import PlatformService
from app.schemas.platform import PlatformInfo, PlatformListResponse
from app.models.platform_store import Platform

router = APIRouter()


@router.get("/platforms", response_model=PlatformListResponse)
async def list_platforms(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List all available platforms with their capabilities and requirements.
    """
    service = PlatformService(db)
    platforms = await service.list_platforms()

    return {
        "platforms": platforms,
        "total": len(platforms),
    }


@router.get("/platforms/{platform}", response_model=PlatformInfo)
async def get_platform_info(
    platform: Platform,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get detailed information about a specific platform.
    """
    service = PlatformService(db)
    info = await service.get_platform_info(platform)

    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform {platform} not found",
        )

    return info
