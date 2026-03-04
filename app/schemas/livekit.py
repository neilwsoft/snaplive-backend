"""LiveKit room and token schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ParticipantType(str, Enum):
    """Participant type for livestreaming"""
    HOST = "host"  # Livestream host (seller)
    VIEWER = "viewer"  # Regular viewer
    AGENT = "agent"  # AI agent


class CreateRoomRequest(BaseModel):
    """Request to create a new live room"""
    room_name: str = Field(..., description="Unique room identifier")
    seller_id: str = Field(..., description="Seller ID hosting the stream")
    max_participants: int = Field(default=100, description="Maximum participants allowed")
    enable_agent: bool = Field(default=True, description="Enable AI agent in the room")


class RoomResponse(BaseModel):
    """Live room information"""
    room_name: str
    seller_id: str
    max_participants: int
    enable_agent: bool
    created_at: Optional[str] = None


class TokenRequest(BaseModel):
    """Request to generate access token for a room"""
    room_name: str = Field(..., description="Room to join")
    participant_name: str = Field(..., description="Participant display name")
    participant_id: str = Field(..., description="Unique participant ID (user_id)")
    participant_type: ParticipantType = Field(default=ParticipantType.VIEWER, description="Participant type")
    can_publish: Optional[bool] = Field(default=None, description="Can publish video/audio (overrides type defaults)")
    can_subscribe: bool = Field(default=True, description="Can receive video/audio")


class TokenResponse(BaseModel):
    """Access token for joining a room"""
    token: str = Field(..., description="JWT access token")
    url: str = Field(..., description="LiveKit server URL")
    room_name: str
    participant_name: str
    participant_type: ParticipantType


class RoomListResponse(BaseModel):
    """List of active rooms"""
    rooms: List[dict]
    total: int
