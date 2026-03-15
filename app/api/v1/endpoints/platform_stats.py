"""Platform Stats API Endpoint

Public endpoint for aggregated platform statistics.
"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.platform_stats_service import PlatformStatsService
from app.schemas.platform_stats import PlatformStatsResponse

router = APIRouter()


def get_platform_stats_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> PlatformStatsService:
    """Dependency to get platform stats service"""
    return PlatformStatsService(db)


@router.get("", response_model=PlatformStatsResponse)
async def get_platform_stats(
    service: PlatformStatsService = Depends(get_platform_stats_service),
):
    """Get aggregated platform statistics (public, no auth required)"""
    stats = await service.get_stats()
    return PlatformStatsResponse(**stats)
