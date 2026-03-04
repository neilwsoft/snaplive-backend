"""LiveKit Egress Service

Manages RTMP egress from LiveKit rooms to external streaming platforms.
Uses RoomCompositeEgress to forward the entire room composition to RTMP destinations.
"""

import logging
from typing import List, Dict, Any, Optional

from livekit.api import (
    LiveKitAPI,
    RoomCompositeEgressRequest,
    StreamOutput,
    StopEgressRequest,
    ListEgressRequest,
    StreamProtocol,
    EncodingOptionsPreset,
    EgressStatus,
)
from app.config import settings

logger = logging.getLogger(__name__)

# Map StreamQuality enum values to LiveKit encoding presets
QUALITY_PRESET_MAP = {
    "low": EncodingOptionsPreset.H264_720P_30,
    "medium": EncodingOptionsPreset.H264_720P_60,
    "high": EncodingOptionsPreset.H264_1080P_30,
    "ultra": EncodingOptionsPreset.H264_1080P_60,
}

# Map EgressStatus enum values to human-readable strings
EGRESS_STATUS_MAP = {
    EgressStatus.EGRESS_STARTING: "starting",
    EgressStatus.EGRESS_ACTIVE: "active",
    EgressStatus.EGRESS_ENDING: "ending",
    EgressStatus.EGRESS_COMPLETE: "complete",
    EgressStatus.EGRESS_FAILED: "failed",
    EgressStatus.EGRESS_ABORTED: "aborted",
    EgressStatus.EGRESS_LIMIT_REACHED: "limit_reached",
}


class EgressService:
    """Service for managing LiveKit RTMP egress"""

    def __init__(self):
        self._livekit_api = None

    @property
    def livekit_api(self) -> LiveKitAPI:
        """Lazy initialization of LiveKit API client"""
        if self._livekit_api is None:
            self._livekit_api = LiveKitAPI(
                url=settings.livekit_url,
                api_key=settings.livekit_api_key,
                api_secret=settings.livekit_api_secret,
            )
        return self._livekit_api

    async def start_room_composite_egress(
        self,
        room_name: str,
        rtmp_urls: List[str],
        quality: str = "high",
    ) -> str:
        """
        Start a RoomCompositeEgress that streams the room to one or more RTMP URLs.

        Args:
            room_name: LiveKit room name
            rtmp_urls: List of full RTMP URLs (including stream key)
            quality: Quality preset key (low/medium/high/ultra)

        Returns:
            egress_id from LiveKit
        """
        preset = QUALITY_PRESET_MAP.get(quality, EncodingOptionsPreset.H264_1080P_30)

        request = RoomCompositeEgressRequest(
            room_name=room_name,
            stream_outputs=[
                StreamOutput(
                    protocol=StreamProtocol.RTMP,
                    urls=rtmp_urls,
                ),
            ],
            preset=preset,
        )

        logger.info(
            f"Starting room composite egress for room={room_name}, "
            f"urls={len(rtmp_urls)}, quality={quality}"
        )

        egress_info = await self.livekit_api.egress.start_room_composite_egress(request)

        logger.info(
            f"Egress started: egress_id={egress_info.egress_id}, "
            f"status={EGRESS_STATUS_MAP.get(egress_info.status, 'unknown')}"
        )

        return egress_info.egress_id

    async def stop_egress(self, egress_id: str) -> Dict[str, Any]:
        """
        Stop a running egress.

        Args:
            egress_id: LiveKit egress ID

        Returns:
            Dict with egress_id and final status
        """
        logger.info(f"Stopping egress: {egress_id}")

        egress_info = await self.livekit_api.egress.stop_egress(
            StopEgressRequest(egress_id=egress_id)
        )

        status_str = EGRESS_STATUS_MAP.get(egress_info.status, "unknown")
        logger.info(f"Egress stopped: egress_id={egress_id}, status={status_str}")

        return {
            "egress_id": egress_info.egress_id,
            "status": status_str,
        }

    async def list_egresses(self, room_name: str) -> List[Dict[str, Any]]:
        """
        List all egresses for a room.

        Args:
            room_name: LiveKit room name

        Returns:
            List of egress info dicts
        """
        response = await self.livekit_api.egress.list_egress(
            ListEgressRequest(room_name=room_name)
        )

        results = []
        for info in response.items:
            results.append({
                "egress_id": info.egress_id,
                "room_name": info.room_name,
                "status": EGRESS_STATUS_MAP.get(info.status, "unknown"),
                "started_at": info.started_at,
                "ended_at": info.ended_at,
                "error": info.error if info.error else None,
            })

        return results


# Singleton instance
egress_service = EgressService()
