"""API v1 router aggregation"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    users,
    notifications,
    inventory,
    logistics,
    orders,
    gifts,
    livekit,
    detection,
    platforms,
    stores,
    streaming,
    livestream_sessions,
    simulcast_presets,
    shipping,
    simulcasters,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(logistics.router, prefix="/logistics", tags=["logistics"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(gifts.router, prefix="/gifts", tags=["gifts"])
api_router.include_router(livekit.router, prefix="/livekit", tags=["livestreaming"])
api_router.include_router(detection.router, prefix="/detection", tags=["detection"])
api_router.include_router(platforms.router, tags=["platforms"])
api_router.include_router(stores.router, tags=["stores"])
api_router.include_router(streaming.router, tags=["streaming"])
api_router.include_router(livestream_sessions.router, prefix="/livestream-sessions", tags=["livestream-sessions"])
api_router.include_router(simulcast_presets.router, prefix="/simulcast-presets", tags=["simulcast-presets"])
api_router.include_router(shipping.router, prefix="/shipping", tags=["shipping"])
api_router.include_router(simulcasters.router, prefix="/simulcasters", tags=["simulcasters"])
