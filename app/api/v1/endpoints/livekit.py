"""LiveKit room and token management endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import json
import logging

from app.schemas.livekit import (
    CreateRoomRequest,
    RoomResponse,
    TokenRequest,
    TokenResponse,
    RoomListResponse,
    ParticipantType
)
from app.services.livekit_service import livekit_service
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/rooms", response_model=RoomResponse, status_code=201)
async def create_room(request: CreateRoomRequest):
    """
    Create a new live streaming room

    - **room_name**: Unique identifier for the room (e.g., "seller-123-stream-20241106")
    - **seller_id**: ID of the seller hosting the stream
    - **max_participants**: Maximum number of viewers allowed
    - **enable_agent**: Whether to enable the AI agent in this room
    """
    try:
        # Prepare room metadata
        metadata = json.dumps({
            "seller_id": request.seller_id,
            "enable_agent": request.enable_agent
        })

        # Create the room
        room = await livekit_service.create_room(
            room_name=request.room_name,
            max_participants=request.max_participants,
            metadata=metadata
        )

        return RoomResponse(
            room_name=room["name"],
            seller_id=request.seller_id,
            max_participants=room["max_participants"],
            enable_agent=request.enable_agent,
            created_at=str(room["creation_time"])
        )

    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")


@router.get("/rooms", response_model=RoomListResponse)
async def list_rooms():
    """
    Get a list of all active live streaming rooms
    """
    try:
        rooms = await livekit_service.list_rooms()
        return RoomListResponse(
            rooms=rooms,
            total=len(rooms)
        )
    except Exception as e:
        logger.error(f"Error listing rooms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list rooms: {str(e)}")


@router.get("/rooms/{room_name}")
async def get_room(room_name: str):
    """
    Get information about a specific room
    """
    try:
        room = await livekit_service.get_room(room_name)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting room: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get room: {str(e)}")


@router.delete("/rooms/{room_name}")
async def delete_room(room_name: str):
    """
    Delete a live streaming room (ends the stream)
    """
    try:
        await livekit_service.delete_room(room_name)
        return {"message": f"Room {room_name} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting room: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete room: {str(e)}")


@router.post("/tokens", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """
    Generate an access token for a participant to join a room

    - **room_name**: Room to join
    - **participant_name**: Display name for the participant
    - **participant_id**: Unique user ID
    - **participant_type**: Type of participant (host, viewer, agent)
    - **can_publish**: Override publish permissions (optional)
    - **can_subscribe**: Can receive video/audio streams

    Default permissions by type:
    - **host**: Can publish and subscribe
    - **viewer**: Can only subscribe
    - **agent**: Can publish and subscribe
    """
    try:
        # Determine publish permissions based on participant type
        if request.can_publish is not None:
            can_publish = request.can_publish
        else:
            # Default permissions by type
            can_publish = request.participant_type in [ParticipantType.HOST, ParticipantType.AGENT]

        # Generate token based on type
        if request.participant_type == ParticipantType.HOST:
            token = livekit_service.generate_host_token(
                room_name=request.room_name,
                host_name=request.participant_name,
                host_id=request.participant_id
            )
        elif request.participant_type == ParticipantType.AGENT:
            token = livekit_service.generate_agent_token(
                room_name=request.room_name
            )
        else:  # VIEWER
            token = livekit_service.generate_viewer_token(
                room_name=request.room_name,
                viewer_name=request.participant_name,
                viewer_id=request.participant_id
            )

        return TokenResponse(
            token=token,
            url=settings.livekit_url,
            room_name=request.room_name,
            participant_name=request.participant_name,
            participant_type=request.participant_type
        )

    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@router.post("/rooms/{room_name}/start-agent")
async def start_agent(room_name: str):
    """
    Start the AI agent in a room

    Note: This generates a token, but you'll need to trigger your LiveKit agent
    worker to actually join the room with this token.
    """
    try:
        # Generate agent token
        token = livekit_service.generate_agent_token(room_name)

        return {
            "message": f"Agent token generated for room {room_name}",
            "token": token,
            "url": settings.livekit_url,
            "note": "Use this token to connect your LiveKit agent worker"
        }
    except Exception as e:
        logger.error(f"Error starting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")
