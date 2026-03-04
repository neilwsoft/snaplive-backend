"""Streaming API Endpoints

Endpoints for managing RTMP streaming destinations and multi-platform broadcasting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.database import get_database
from app.services.streaming_service import StreamingService
from app.services.platform_service import PlatformService
from app.schemas.sync import (
    StreamingDestinationCreate,
    StreamingDestinationUpdate,
    StreamingDestinationResponse,
    StreamingDestinationListResponse,
    StartEgressRequest,
    EgressBatchResponse,
    EgressResult,
    EgressStatusResponse,
    EgressStatusInfo,
)
from app.models.stream_destination import Platform
from app.services.egress_service import egress_service

router = APIRouter()


@router.post("/streaming/destinations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_streaming_destination(
    destination: StreamingDestinationCreate,
    seller_id: str = Query(..., description="Seller ID"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a new RTMP streaming destination.
    """
    service = StreamingService(db)

    result = await service.create_destination(
        seller_id=seller_id,
        platform=destination.platform,
        destination_name=destination.destination_name,
        rtmp_url=destination.rtmp_url,
        stream_key=destination.stream_key,
        store_id=destination.store_id,
        backup_rtmp_url=destination.backup_rtmp_url,
        backup_stream_key=destination.backup_stream_key,
        quality=destination.quality,
        bitrate_kbps=destination.bitrate_kbps,
        fps=destination.fps,
        resolution_width=destination.resolution_width,
        resolution_height=destination.resolution_height,
        audio_bitrate_kbps=destination.audio_bitrate_kbps,
        audio_sample_rate=destination.audio_sample_rate,
        platform_settings=destination.platform_settings,
    )

    return result


@router.get("/streaming/destinations", response_model=StreamingDestinationListResponse)
async def list_streaming_destinations(
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    platform: Optional[Platform] = Query(None, description="Filter by platform"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List all streaming destinations.
    """
    service = StreamingService(db)
    destinations = await service.list_destinations(
        seller_id=seller_id,
        store_id=store_id,
        platform=platform,
        is_enabled=is_enabled,
    )

    return {
        "destinations": destinations,
        "total": len(destinations),
    }


@router.get("/streaming/destinations/{destination_id}", response_model=StreamingDestinationResponse)
async def get_streaming_destination(
    destination_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get a specific streaming destination.
    """
    service = StreamingService(db)
    destination = await service.get_destination(destination_id)

    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Streaming destination not found",
        )

    # Add computed fields
    destination["has_backup"] = bool(destination.get("backup_rtmp_url"))
    destination["is_streaming"] = destination.get("status") == "streaming"

    return destination


@router.put("/streaming/destinations/{destination_id}", response_model=dict)
async def update_streaming_destination(
    destination_id: str,
    updates: StreamingDestinationUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update a streaming destination.
    """
    service = StreamingService(db)

    # Build updates dict
    update_dict = {}
    if updates.destination_name is not None:
        update_dict["destination_name"] = updates.destination_name
    if updates.rtmp_url is not None:
        update_dict["rtmp_url"] = updates.rtmp_url
    if updates.stream_key is not None:
        update_dict["stream_key"] = updates.stream_key
    if updates.backup_rtmp_url is not None:
        update_dict["backup_rtmp_url"] = updates.backup_rtmp_url
    if updates.backup_stream_key is not None:
        update_dict["backup_stream_key"] = updates.backup_stream_key
    if updates.quality is not None:
        update_dict["quality"] = updates.quality
    if updates.bitrate_kbps is not None:
        update_dict["bitrate_kbps"] = updates.bitrate_kbps
    if updates.fps is not None:
        update_dict["fps"] = updates.fps
    if updates.is_enabled is not None:
        update_dict["is_enabled"] = updates.is_enabled
    if updates.platform_settings is not None:
        update_dict["platform_settings"] = updates.platform_settings

    result = await service.update_destination(destination_id, update_dict)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"],
        )

    return result


@router.delete("/streaming/destinations/{destination_id}", response_model=dict)
async def delete_streaming_destination(
    destination_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Delete a streaming destination.
    """
    service = StreamingService(db)
    result = await service.delete_destination(destination_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


@router.get("/streaming/stores/{store_id}/rtmp-config", response_model=dict)
async def get_store_rtmp_config(
    store_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get RTMP configuration from platform for a specific store.
    """
    service = StreamingService(db)
    result = await service.get_rtmp_config_for_store(store_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


@router.post("/streaming/destinations/{destination_id}/start", response_model=dict)
async def start_streaming(
    destination_id: str,
    room_name: str = Query(..., description="LiveKit room name"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Start streaming to a destination.
    """
    service = StreamingService(db)
    result = await service.start_stream(destination_id, room_name)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


@router.post("/streaming/destinations/{destination_id}/end", response_model=dict)
async def end_streaming(
    destination_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    End streaming to a destination.
    """
    service = StreamingService(db)
    result = await service.end_stream(destination_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return result


@router.get("/streaming/active", response_model=StreamingDestinationListResponse)
async def get_active_streams(
    seller_id: Optional[str] = Query(None, description="Filter by seller ID"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get all currently active streaming destinations.
    """
    service = StreamingService(db)
    destinations = await service.get_active_destinations(seller_id)

    return {
        "destinations": destinations,
        "total": len(destinations),
    }


@router.get("/streaming/reports", response_model=dict)
async def get_streaming_reports(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get aggregated streaming reports (connectivity, latency, etc).
    """
    service = StreamingService(db)
    reports = await service.get_streaming_reports()
    
    return reports


@router.post("/streaming/destinations/{destination_id}/metrics", response_model=dict)
async def update_stream_metrics(
    destination_id: str,
    metrics: dict,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update real-time streaming metrics for a destination.
    """
    service = StreamingService(db)
    result = await service.update_stream_metrics(destination_id, metrics)

    return result


@router.post("/streaming/destinations/{destination_id}/error", response_model=dict)
async def report_stream_error(
    destination_id: str,
    error_message: str = Query(..., description="Error message"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Report a streaming error for a destination.
    """
    service = StreamingService(db)
    result = await service.handle_stream_error(destination_id, error_message)

    return result


# --- Batch Egress Endpoints ---


@router.post("/streaming/egress/start", response_model=EgressBatchResponse)
async def start_egress_batch(
    request: StartEgressRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Start RTMP egress for multiple destinations at once.
    Each destination will be streamed via LiveKit RoomCompositeEgress.
    """
    service = StreamingService(db)
    results = []

    for dest_id in request.destination_ids:
        try:
            result = await service.start_stream(dest_id, request.room_name)
            results.append(EgressResult(
                destination_id=dest_id,
                success=result.get("success", False),
                egress_id=result.get("egress_id"),
                error=result.get("message") if not result.get("success") else None,
            ))
        except Exception as e:
            results.append(EgressResult(
                destination_id=dest_id,
                success=False,
                error=str(e),
            ))

    return EgressBatchResponse(results=results)


@router.post("/streaming/egress/stop/{room_name}", response_model=EgressBatchResponse)
async def stop_egress_batch(
    room_name: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Stop all active egresses for a room.
    Finds all streaming destinations associated with the room and stops their egress.
    """
    service = StreamingService(db)
    results = []

    # Find all destinations currently streaming to this room
    destinations = await service.destinations_collection.find({
        "current_stream_id": room_name,
        "status": "streaming",
    }).to_list(length=100)

    for dest in destinations:
        dest_id = str(dest["_id"])
        try:
            result = await service.end_stream(dest_id)
            results.append(EgressResult(
                destination_id=dest_id,
                success=result.get("success", False),
                platform=dest.get("platform"),
                error=result.get("message") if not result.get("success") else None,
            ))
        except Exception as e:
            results.append(EgressResult(
                destination_id=dest_id,
                success=False,
                platform=dest.get("platform"),
                error=str(e),
            ))

    return EgressBatchResponse(results=results)


@router.get("/streaming/egress/{room_name}/status", response_model=EgressStatusResponse)
async def get_egress_status(
    room_name: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get egress status for a room.
    Returns status from LiveKit combined with destination metadata.
    """
    service = StreamingService(db)

    # Get egress info from LiveKit
    try:
        egresses = await egress_service.list_egresses(room_name)
    except Exception:
        egresses = []

    # Build a map of egress_id → destination for enrichment
    destinations = await service.destinations_collection.find({
        "current_stream_id": room_name,
    }).to_list(length=100)

    egress_to_dest = {}
    for dest in destinations:
        if dest.get("egress_id"):
            egress_to_dest[dest["egress_id"]] = dest

    results = []
    for eg in egresses:
        dest = egress_to_dest.get(eg["egress_id"])
        results.append(EgressStatusInfo(
            egress_id=eg["egress_id"],
            status=eg["status"],
            destination_id=str(dest["_id"]) if dest else None,
            platform=dest.get("platform") if dest else None,
            started_at=eg.get("started_at"),
            ended_at=eg.get("ended_at"),
            error=eg.get("error"),
        ))

    return EgressStatusResponse(egresses=results)
