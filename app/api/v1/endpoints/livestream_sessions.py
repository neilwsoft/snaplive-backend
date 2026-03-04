"""Livestream Session API Endpoints

API routes for livestream session management operations.

IMPORTANT: Route order matters in FastAPI!
All specific routes (e.g., /public, /room, /seed, /seller) MUST be defined
BEFORE catch-all routes like /{session_id} to avoid conflicts.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.livestream_session_service import LivestreamSessionService
from app.schemas.livestream_session import (
    LivestreamSessionCreate,
    LivestreamSessionUpdate,
    LivestreamSessionResponse,
    LivestreamSessionListResponse,
    SessionProductResponse,
    SessionStatsResponse,
    SessionStatsUpdate,
    StartSessionRequest,
    EndSessionRequest,
    LiveStatsResponse
)

router = APIRouter()


def get_session_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> LivestreamSessionService:
    """Dependency to get livestream session service"""
    return LivestreamSessionService(db)


def _session_to_response(session) -> LivestreamSessionResponse:
    """Convert session model to response"""
    return LivestreamSessionResponse(
        _id=str(session.id),
        seller_id=session.seller_id,
        room_name=session.room_name,
        title=session.title,
        description=session.description,
        thumbnail_url=getattr(session, 'thumbnail_url', None),
        status=session.status,
        products=[SessionProductResponse(**p.model_dump()) for p in session.products],
        product_count=session.product_count,
        max_participants=session.max_participants,
        enable_agent=session.enable_agent,
        created_at=session.created_at,
        updated_at=session.updated_at,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        stats=SessionStatsResponse(**session.stats.model_dump())
    )


# ==============================================================================
# SPECIFIC ROUTES (must come before /{session_id} catch-all)
# ==============================================================================

# Public Endpoints (No Authentication Required)

@router.get("/public", response_model=LivestreamSessionListResponse)
async def list_public_sessions(
    category: Optional[str] = Query(None, description="Filter by category"),
    platform: Optional[str] = Query(None, description="Filter by platform (douyin, xiaohongshu, taobao, snaplive)"),
    status: Optional[str] = Query("live", description="Filter by status (default: live)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    service: LivestreamSessionService = Depends(get_session_service)
):
    """List public livestream sessions for guest users (no auth required).

    Returns active/live sessions that guests can browse before logging in.
    Supports filtering by category and platform.
    """
    skip = (page - 1) * page_size

    # For public endpoint, we only show live or ended sessions (not pending/cancelled)
    allowed_statuses = ["live", "ended"]
    if status and status not in allowed_statuses:
        status = "live"

    items, total = await service.list_sessions(
        seller_id=None,  # All sellers
        status=status,
        category=category,
        platform=platform,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return LivestreamSessionListResponse(
        items=[_session_to_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# Room-based lookup

@router.get("/room/{room_name}", response_model=LivestreamSessionResponse)
async def get_session_by_room(
    room_name: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Get a livestream session by room name"""
    session = await service.get_session_by_room_name(room_name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session)


# Seller statistics

@router.get("/seller/{seller_id}/stats")
async def get_seller_stats(
    seller_id: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Get aggregate statistics for a seller"""
    stats = await service.get_seller_stats(seller_id)
    return stats


# Seed Endpoint (Development only)

@router.post("/seed", response_model=list[LivestreamSessionResponse])
async def seed_dummy_sessions(
    seller_id: str = Query(..., description="Seller ID to create sessions for"),
    count: int = Query(10, ge=1, le=50, description="Number of sessions to create"),
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Seed dummy ended sessions for history testing (development only)"""
    sessions = await service.seed_dummy_sessions(seller_id, count)
    return [_session_to_response(s) for s in sessions]


# ==============================================================================
# BASE CRUD ENDPOINTS
# ==============================================================================

@router.post("", response_model=LivestreamSessionResponse, status_code=201)
async def create_session(
    session_data: LivestreamSessionCreate,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Create a new livestream session"""
    session = await service.create_session(session_data)
    return _session_to_response(session)


@router.get("", response_model=LivestreamSessionListResponse)
async def list_sessions(
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, live, ended, cancelled)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: LivestreamSessionService = Depends(get_session_service)
):
    """List livestream sessions with filters and pagination"""
    skip = (page - 1) * page_size

    items, total = await service.list_sessions(
        seller_id=seller_id,
        status=status,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size

    return LivestreamSessionListResponse(
        items=[_session_to_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# ==============================================================================
# PARAMETERIZED ROUTES (/{session_id} - must come LAST)
# ==============================================================================

@router.get("/{session_id}", response_model=LivestreamSessionResponse)
async def get_session(
    session_id: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Get a livestream session by ID"""
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session)


@router.patch("/{session_id}", response_model=LivestreamSessionResponse)
async def update_session(
    session_id: str,
    update_data: LivestreamSessionUpdate,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Update a livestream session"""
    session = await service.update_session(session_id, update_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Delete a livestream session"""
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


# Status Transition Endpoints

@router.post("/{session_id}/start", response_model=LivestreamSessionResponse)
async def start_session(
    session_id: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Start a livestream session (transition from pending to live)"""
    try:
        session = await service.start_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return _session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/end", response_model=LivestreamSessionResponse)
async def end_session(
    session_id: str,
    end_data: Optional[EndSessionRequest] = None,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """End a livestream session (transition from live to ended)"""
    try:
        stats_update = end_data.stats if end_data else None
        session = await service.end_session(session_id, stats_update)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return _session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/cancel", response_model=LivestreamSessionResponse)
async def cancel_session(
    session_id: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Cancel a livestream session (only if pending)"""
    try:
        session = await service.cancel_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return _session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Statistics Endpoints

@router.patch("/{session_id}/stats", response_model=LivestreamSessionResponse)
async def update_session_stats(
    session_id: str,
    stats_data: SessionStatsUpdate,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Update session statistics"""
    session = await service.update_stats(session_id, stats_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(session)


@router.get("/{session_id}/live-stats", response_model=LiveStatsResponse)
async def get_live_stats(
    session_id: str,
    service: LivestreamSessionService = Depends(get_session_service)
):
    """Get real-time statistics for an active livestream session.

    Returns aggregated stats including:
    - Orders and revenue from the current session
    - Viewer counts and conversion rate
    - Hourly viewer breakdown
    - Channel performance (Douyin, Xiaohongshu, Taobao)
    - Social engagement stats
    """
    stats = await service.get_live_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found or not active")
    return stats
