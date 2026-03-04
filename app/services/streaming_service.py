"""Streaming Service

Business logic for managing RTMP streaming destinations and multi-platform broadcasting.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.stream_destination import (
    StreamDestination,
    Platform,
    StreamProtocol,
    StreamStatus,
    StreamQuality,
)
from app.models.stream_metric import StreamMetric
from app.services.platform_service import PlatformService
from app.services.egress_service import egress_service

import logging

logger = logging.getLogger(__name__)


class StreamingService:
    """Service for streaming destination management"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.destinations_collection = db.stream_destinations
        self.stores_collection = db.platform_stores
        self.metrics_collection = db.stream_metrics
        self.platform_service = PlatformService(db)

    async def create_destination(
        self,
        seller_id: str,
        platform: Platform,
        destination_name: str,
        rtmp_url: str,
        stream_key: str,
        store_id: Optional[str] = None,
        backup_rtmp_url: Optional[str] = None,
        backup_stream_key: Optional[str] = None,
        quality: StreamQuality = StreamQuality.HIGH,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a new streaming destination"""

        destination_data = {
            "seller_id": ObjectId(seller_id),
            "store_id": ObjectId(store_id) if store_id else None,
            "platform": platform.value,
            "destination_name": destination_name,
            "protocol": StreamProtocol.RTMP.value,
            "rtmp_url": rtmp_url,
            "stream_key": stream_key,  # Should be encrypted in production
            "backup_rtmp_url": backup_rtmp_url,
            "backup_stream_key": backup_stream_key,  # Should be encrypted
            "quality": quality.value if hasattr(quality, 'value') else quality,
            "bitrate_kbps": kwargs.get("bitrate_kbps", 4000),
            "fps": kwargs.get("fps", 30),
            "resolution_width": kwargs.get("resolution_width", 1920),
            "resolution_height": kwargs.get("resolution_height", 1080),
            "audio_bitrate_kbps": kwargs.get("audio_bitrate_kbps", 128),
            "audio_sample_rate": kwargs.get("audio_sample_rate", 44100),
            "status": StreamStatus.INACTIVE.value,
            "is_enabled": True,
            "total_streams": 0,
            "successful_streams": 0,
            "failed_streams": 0,
            "platform_settings": kwargs.get("platform_settings", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await self.destinations_collection.insert_one(destination_data)

        return {
            "success": True,
            "destination_id": str(result.inserted_id),
            "message": f"Streaming destination created for {platform.value}",
        }

    async def get_destination(self, destination_id: str) -> Optional[Dict[str, Any]]:
        """Get a streaming destination by ID"""
        destination = await self.destinations_collection.find_one(
            {"_id": ObjectId(destination_id)}
        )
        if destination:
            destination["_id"] = str(destination["_id"])
            destination["seller_id"] = str(destination["seller_id"])
            if destination.get("store_id"):
                destination["store_id"] = str(destination["store_id"])
        return destination

    async def list_destinations(
        self,
        seller_id: Optional[str] = None,
        store_id: Optional[str] = None,
        platform: Optional[Platform] = None,
        is_enabled: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """List streaming destinations"""
        query = {}
        if seller_id:
            query["seller_id"] = ObjectId(seller_id)
        if store_id:
            query["store_id"] = ObjectId(store_id)
        if platform:
            query["platform"] = platform.value
        if is_enabled is not None:
            query["is_enabled"] = is_enabled

        destinations = await self.destinations_collection.find(query).to_list(length=100)

        # Convert ObjectIds to strings and map fields for response schema
        for dest in destinations:
            dest["id"] = str(dest.pop("_id"))
            dest["seller_id"] = str(dest["seller_id"])
            if dest.get("store_id"):
                dest["store_id"] = str(dest["store_id"])
            # Remove sensitive stream keys from list view
            dest["stream_key"] = "***" + dest["stream_key"][-4:] if dest.get("stream_key") else None
            if dest.get("backup_stream_key"):
                dest["backup_stream_key"] = "***" + dest["backup_stream_key"][-4:]
            # Compute derived fields
            dest["has_backup"] = bool(dest.get("backup_rtmp_url"))
            dest["is_streaming"] = dest.get("status") == "streaming"

        return destinations

    async def update_destination(
        self,
        destination_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a streaming destination"""
        updates["updated_at"] = datetime.utcnow()

        result = await self.destinations_collection.update_one(
            {"_id": ObjectId(destination_id)},
            {"$set": updates}
        )

        if result.modified_count > 0:
            return {"success": True, "message": "Destination updated successfully"}
        else:
            return {"success": False, "message": "Destination not found or no changes made"}

    async def delete_destination(self, destination_id: str) -> Dict[str, Any]:
        """Delete a streaming destination"""
        # Check if destination is currently streaming
        destination = await self.get_destination(destination_id)
        if not destination:
            return {"success": False, "message": "Destination not found"}

        if destination.get("status") == StreamStatus.STREAMING.value:
            return {
                "success": False,
                "message": "Cannot delete a destination that is currently streaming",
            }

        await self.destinations_collection.delete_one({"_id": ObjectId(destination_id)})
        return {"success": True, "message": "Destination deleted successfully"}

    async def get_rtmp_config_for_store(self, store_id: str) -> Dict[str, Any]:
        """Get RTMP configuration from platform adapter for a store"""
        store, adapter = await self.platform_service.get_store_with_adapter(store_id)
        if not store or not adapter:
            return {
                "success": False,
                "message": "Store not found or invalid connection",
            }

        # Get RTMP config from platform adapter
        config = await adapter.get_rtmp_config(store["store_id"])

        return {
            "success": True,
            "platform": store["platform"],
            "config": config,
        }

    async def start_stream(
        self,
        destination_id: str,
        room_name: str,
    ) -> Dict[str, Any]:
        """Mark a stream as started on a destination"""
        destination = await self.get_destination(destination_id)
        if not destination:
            return {"success": False, "message": "Destination not found"}

        if not destination.get("is_enabled"):
            return {"success": False, "message": "Destination is disabled"}

        # Update destination status
        await self.destinations_collection.update_one(
            {"_id": ObjectId(destination_id)},
            {
                "$set": {
                    "status": StreamStatus.STREAMING.value,
                    "current_stream_id": room_name,
                    "stream_started_at": datetime.utcnow(),
                    "last_used_at": datetime.utcnow(),
                },
                "$inc": {"total_streams": 1},
            }
        )

        # If there's a store, notify the platform
        if destination.get("store_id"):
            store, adapter = await self.platform_service.get_store_with_adapter(
                destination["store_id"]
            )
            if adapter:
                stream_config = {
                    "title": f"Live Stream - {room_name}",
                    "room_name": room_name,
                }
                await adapter.start_live_stream(store["store_id"], stream_config)

        # Start RTMP egress via LiveKit
        egress_id = None
        rtmp_full_url = f"{destination['rtmp_url']}/{destination['stream_key']}"
        try:
            egress_id = await egress_service.start_room_composite_egress(
                room_name=room_name,
                rtmp_urls=[rtmp_full_url],
                quality=destination.get("quality", "high"),
            )
            await self.destinations_collection.update_one(
                {"_id": ObjectId(destination_id)},
                {"$set": {"egress_id": egress_id}},
            )
        except Exception as e:
            logger.error(f"Failed to start egress for destination {destination_id}: {e}")
            await self.handle_stream_error(destination_id, f"Egress start failed: {e}")
            return {
                "success": False,
                "message": f"Egress start failed: {e}",
            }

        return {
            "success": True,
            "message": "Stream started",
            "rtmp_url": destination["rtmp_url"],
            "stream_key": destination["stream_key"],
            "egress_id": egress_id,
        }

    async def end_stream(
        self,
        destination_id: str,
    ) -> Dict[str, Any]:
        """Mark a stream as ended on a destination"""
        destination = await self.get_destination(destination_id)
        if not destination:
            return {"success": False, "message": "Destination not found"}

        if destination.get("status") != StreamStatus.STREAMING.value:
            return {"success": False, "message": "Destination is not currently streaming"}

        # Stop RTMP egress if active
        if destination.get("egress_id"):
            try:
                await egress_service.stop_egress(destination["egress_id"])
            except Exception as e:
                logger.warning(f"Failed to stop egress {destination['egress_id']}: {e}")

        # Determine if stream was successful
        # In a real implementation, you would check for errors during streaming
        was_successful = True

        # Update destination status
        update_fields = {
            "status": StreamStatus.INACTIVE.value,
            "stream_ended_at": datetime.utcnow(),
            "current_stream_id": None,
            "egress_id": None,
        }

        inc_fields = {}
        if was_successful:
            inc_fields["successful_streams"] = 1
        else:
            inc_fields["failed_streams"] = 1

        # Calculate duration
        start_time = destination.get("stream_started_at")
        if start_time:
            duration = (update_fields["stream_ended_at"] - start_time).total_seconds()
            inc_fields["total_streaming_seconds"] = duration
            if was_successful:
                inc_fields["successful_streaming_seconds"] = duration

        await self.destinations_collection.update_one(
            {"_id": ObjectId(destination_id)},
            {
                "$set": update_fields,
                "$inc": inc_fields,
            }
        )

        # If there's a store, notify the platform
        final_metrics = None
        if destination.get("store_id") and destination.get("current_stream_id"):
            store, adapter = await self.platform_service.get_store_with_adapter(
                destination["store_id"]
            )
            if adapter:
                result = await adapter.end_live_stream(
                    store["store_id"],
                    destination["current_stream_id"]
                )
                final_metrics = result.get("final_metrics")

        return {
            "success": True,
            "message": "Stream ended",
            "final_metrics": final_metrics,
        }

    async def get_active_destinations(self, seller_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all currently streaming destinations"""
        query = {"status": StreamStatus.STREAMING.value}
        if seller_id:
            query["seller_id"] = ObjectId(seller_id)

        destinations = await self.destinations_collection.find(query).to_list(length=100)

        # Convert ObjectIds to strings
        for dest in destinations:
            dest["_id"] = str(dest["_id"])
            dest["seller_id"] = str(dest["seller_id"])
            if dest.get("store_id"):
                dest["store_id"] = str(dest["store_id"])

        return destinations

    async def update_stream_metrics(
        self,
        destination_id: str,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update real-time streaming metrics for a destination"""
        
        # Get destination to know the platform
        destination = await self.get_destination(destination_id)
        if not destination:
            return {"success": False, "message": "Destination not found"}

        update_fields = {}
        if "bitrate_kbps" in metrics:
            update_fields["average_bitrate_kbps"] = metrics["bitrate_kbps"]
        if "dropped_frames" in metrics:
            update_fields["dropped_frames_count"] = metrics["dropped_frames"]

        if update_fields:
            await self.destinations_collection.update_one(
                {"_id": ObjectId(destination_id)},
                {"$set": update_fields}
            )

        # Record historical metric
        try:
            metric = StreamMetric(
                destination_id=ObjectId(destination_id),
                platform=destination.get("platform", "custom"),
                timestamp=datetime.utcnow(),
                latency_ms=metrics.get("latency_ms", 0),
                bitrate_kbps=metrics.get("bitrate_kbps", 0),
                fps=metrics.get("fps"),
                dropped_frames=metrics.get("dropped_frames", 0)
            )
            await self.metrics_collection.insert_one(metric.model_dump())
        except Exception as e:
            print(f"Failed to record stream metric: {e}")

        return {"success": True, "message": "Metrics updated"}

    async def get_streaming_reports(self) -> Dict[str, Any]:
        """Get aggregated streaming reports for dashboard"""
        
        # 1. Connectivity Stats (from StreamDestinations)
        destinations = await self.destinations_collection.find({}).to_list(length=1000)
        
        platform_stats = {}
        for dest in destinations:
            platform = dest.get("platform", "custom")
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "total_streams": 0,
                    "successful_streams": 0,
                    "total_seconds": 0,
                    "successful_seconds": 0
                }
            
            platform_stats[platform]["total_streams"] += dest.get("total_streams", 0)
            platform_stats[platform]["successful_streams"] += dest.get("successful_streams", 0)
            platform_stats[platform]["total_seconds"] += dest.get("total_streaming_seconds", 0)
            platform_stats[platform]["successful_seconds"] += dest.get("successful_streaming_seconds", 0)

        connectivity_stats = []
        for platform, stats in platform_stats.items():
            total = stats["total_streams"]
            successful_time_hours = stats["successful_seconds"] / 3600
            total_time_hours = stats["total_seconds"] / 3600
            
            # If no time data yet, fallback to estimating 1 hour per stream (only if count > 0)
            if total_time_hours == 0 and total > 0:
                total_time_hours = total
                successful_time_hours = stats["successful_streams"]
            
            rate = (stats["successful_streams"] / total * 100) if total > 0 else 0
            
            connectivity_stats.append({
                "platform": platform,
                "rate": rate,
                "successfulTime": round(successful_time_hours, 1),
                "scheduledTime": round(total_time_hours, 1)
            })

        # 2. Latency Stats (from StreamMetrics)
        latency_stats = []
        platforms = list(platform_stats.keys()) if platform_stats else ["douyin", "xiaohongshu", "taobao"]
        
        for platform in platforms:
            # Get last 12 metrics for this platform
            # We need to find destinations for this platform first
            platform_dest_ids = [d["_id"] for d in destinations if d.get("platform") == platform]
            
            if not platform_dest_ids:
                continue

            cursor = self.metrics_collection.find(
                {"destination_id": {"$in": platform_dest_ids}}
            ).sort("timestamp", -1).limit(12)
            
            metrics = await cursor.to_list(length=12)
            metrics.reverse() # chronological order
            
            data_points = []
            total_latency = 0
            count = 0
            
            for m in metrics:
                lat = m.get("latency_ms", 0)
                data_points.append({
                    "timestamp": m.get("timestamp").isoformat(),
                    "latency": lat
                })
                total_latency += lat
                count += 1
            
            avg_latency = (total_latency / count) if count > 0 else 0
            
            latency_stats.append({
                "platform": platform,
                "averageLatency": avg_latency,
                "dataPoints": data_points
            })

        return {
            "connectivity": connectivity_stats,
            "latency": latency_stats
        }

    async def handle_stream_error(
        self,
        destination_id: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """Handle streaming errors"""
        await self.destinations_collection.update_one(
            {"_id": ObjectId(destination_id)},
            {
                "$set": {
                    "status": StreamStatus.ERROR.value,
                    "connection_error": error_message,
                    "last_error_message": error_message,
                },
                "$inc": {"failed_streams": 1},
            }
        )

        return {"success": True, "message": "Error recorded"}
