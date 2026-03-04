"""LiveKit room and token management service"""

import logging
from typing import Optional, Dict, Any
from livekit.api import LiveKitAPI, AccessToken, VideoGrants
from livekit.protocol import room as proto_room
from app.config import settings

logger = logging.getLogger(__name__)


class LiveKitService:
    """Service for managing LiveKit rooms and tokens"""

    def __init__(self):
        """Initialize LiveKit API client"""
        self._livekit_api = None

    @property
    def livekit_api(self):
        """Lazy initialization of LiveKit API client"""
        if self._livekit_api is None:
            self._livekit_api = LiveKitAPI(
                url=settings.livekit_url,
                api_key=settings.livekit_api_key,
                api_secret=settings.livekit_api_secret
            )
        return self._livekit_api

    async def create_room(
        self,
        room_name: str,
        max_participants: int = 100,
        metadata: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new LiveKit room

        Args:
            room_name: Unique room identifier
            max_participants: Maximum number of participants
            metadata: Optional room metadata (JSON string)

        Returns:
            Room information dictionary
        """
        try:
            room = await self.livekit_api.room.create_room(
                proto_room.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=60 * 10,  # 10 minutes until room closes when empty
                    max_participants=max_participants,
                    metadata=metadata or ""
                )
            )
            logger.info(f"Created LiveKit room: {room_name}")
            return {
                "sid": room.sid,
                "name": room.name,
                "max_participants": room.max_participants,
                "creation_time": room.creation_time,
                "metadata": room.metadata
            }
        except Exception as e:
            logger.error(f"Failed to create room {room_name}: {str(e)}")
            raise

    async def list_rooms(self) -> list:
        """
        List all active LiveKit rooms

        Returns:
            List of room dictionaries
        """
        try:
            rooms = await self.livekit_api.room.list_rooms(proto_room.ListRoomsRequest())
            return [
                {
                    "sid": room.sid,
                    "name": room.name,
                    "num_participants": room.num_participants,
                    "max_participants": room.max_participants,
                    "creation_time": room.creation_time,
                    "metadata": room.metadata
                }
                for room in rooms.rooms
            ]
        except Exception as e:
            logger.error(f"Failed to list rooms: {str(e)}")
            raise

    async def get_room(self, room_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific room

        Args:
            room_name: Room identifier

        Returns:
            Room information or None if not found
        """
        try:
            # Try to list rooms with a filter (more efficient than listing all)
            rooms = await self.livekit_api.room.list_rooms(
                proto_room.ListRoomsRequest(names=[room_name])
            )

            if rooms.rooms and len(rooms.rooms) > 0:
                room = rooms.rooms[0]
                return {
                    "sid": room.sid,
                    "name": room.name,
                    "num_participants": room.num_participants,
                    "max_participants": room.max_participants,
                    "creation_time": room.creation_time,
                    "metadata": room.metadata
                }

            logger.warning(f"Room {room_name} not found")
            return None

        except Exception as e:
            logger.error(f"Failed to get room {room_name}: {str(e)}")
            return None

    async def delete_room(self, room_name: str) -> bool:
        """
        Delete a LiveKit room

        Args:
            room_name: Room to delete

        Returns:
            True if successful
        """
        try:
            await self.livekit_api.room.delete_room(
                proto_room.DeleteRoomRequest(room=room_name)
            )
            logger.info(f"Deleted LiveKit room: {room_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete room {room_name}: {str(e)}")
            raise

    def generate_token(
        self,
        room_name: str,
        participant_name: str,
        participant_identity: str,
        can_publish: bool = False,
        can_subscribe: bool = True,
        can_publish_data: bool = True,
        metadata: Optional[str] = None
    ) -> str:
        """
        Generate an access token for a participant to join a room

        Args:
            room_name: Room to join
            participant_name: Display name
            participant_identity: Unique participant ID
            can_publish: Can publish video/audio
            can_subscribe: Can receive video/audio
            can_publish_data: Can send data messages
            metadata: Optional participant metadata

        Returns:
            JWT access token
        """
        try:
            token = AccessToken(
                settings.livekit_api_key,
                settings.livekit_api_secret
            )
            token.with_identity(participant_identity)
            token.with_name(participant_name)

            if metadata:
                token.with_metadata(metadata)

            # Set video grants (permissions)
            token.with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=can_publish,
                can_subscribe=can_subscribe,
                can_publish_data=can_publish_data
            ))

            jwt_token = token.to_jwt()
            logger.info(f"Generated token for {participant_name} in room {room_name}")
            return jwt_token

        except Exception as e:
            logger.error(f"Failed to generate token: {str(e)}")
            raise

    def generate_host_token(
        self,
        room_name: str,
        host_name: str,
        host_id: str
    ) -> str:
        """
        Generate token for livestream host (can publish)

        Args:
            room_name: Room name
            host_name: Host display name
            host_id: Host user ID

        Returns:
            JWT access token
        """
        return self.generate_token(
            room_name=room_name,
            participant_name=host_name,
            participant_identity=host_id,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
            metadata='{"type": "host"}'
        )

    def generate_viewer_token(
        self,
        room_name: str,
        viewer_name: str,
        viewer_id: str
    ) -> str:
        """
        Generate token for viewer (can only subscribe)

        Args:
            room_name: Room name
            viewer_name: Viewer display name
            viewer_id: Viewer user ID

        Returns:
            JWT access token
        """
        return self.generate_token(
            room_name=room_name,
            participant_name=viewer_name,
            participant_identity=viewer_id,
            can_publish=False,
            can_subscribe=True,
            can_publish_data=True,
            metadata='{"type": "viewer"}'
        )

    def generate_agent_token(
        self,
        room_name: str
    ) -> str:
        """
        Generate token for AI agent (can publish audio/video)

        Args:
            room_name: Room name

        Returns:
            JWT access token
        """
        return self.generate_token(
            room_name=room_name,
            participant_name="AI Assistant",
            participant_identity=f"agent-{room_name}",
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
            metadata='{"type": "agent"}'
        )


# Singleton instance
livekit_service = LiveKitService()
