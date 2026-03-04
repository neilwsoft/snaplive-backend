"""Analytics service for tracking object detection events"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.detection import DetectionAnalytics, Detection, BoundingBox

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and analyzing object detection data"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.analytics_collection = db.detection_analytics

    async def track_detection(
        self,
        room_id: str,
        session_id: str,
        detection: Detection,
        duration_seconds: float = 0.0
    ) -> str:
        """
        Track a detection event

        Args:
            room_id: Live room identifier
            session_id: Streaming session ID
            detection: Detection result
            duration_seconds: How long object was visible

        Returns:
            Inserted document ID
        """
        try:
            analytics_record = DetectionAnalytics(
                room_id=room_id,
                session_id=session_id,
                product_id=detection.matched_product_id,
                detected_class=detection.class_name,
                confidence=detection.confidence,
                detected_at=datetime.utcnow(),
                duration_seconds=duration_seconds,
                bounding_box=detection.box
            )

            result = await self.analytics_collection.insert_one(
                analytics_record.model_dump(by_alias=True, exclude={"id"})
            )

            logger.info(
                f"Tracked detection: {detection.class_name} "
                f"(confidence: {detection.confidence:.2f}) "
                f"in room {room_id}"
            )

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to track detection: {str(e)}")
            raise

    async def batch_track_detections(
        self,
        room_id: str,
        session_id: str,
        detections: List[Detection]
    ) -> int:
        """
        Track multiple detections in a single batch

        Args:
            room_id: Live room identifier
            session_id: Streaming session ID
            detections: List of detection results

        Returns:
            Number of records inserted
        """
        try:
            if not detections:
                return 0

            records = [
                DetectionAnalytics(
                    room_id=room_id,
                    session_id=session_id,
                    product_id=det.matched_product_id,
                    detected_class=det.class_name,
                    confidence=det.confidence,
                    detected_at=datetime.utcnow(),
                    duration_seconds=0.0,
                    bounding_box=det.box
                ).model_dump(by_alias=True, exclude={"id"})
                for det in detections
            ]

            result = await self.analytics_collection.insert_many(records)
            count = len(result.inserted_ids)

            logger.info(f"Batch tracked {count} detections in room {room_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to batch track detections: {str(e)}")
            raise

    async def get_session_analytics(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all detection events for a session

        Args:
            session_id: Streaming session ID

        Returns:
            List of detection records
        """
        try:
            cursor = self.analytics_collection.find(
                {"session_id": session_id}
            ).sort("detected_at", 1)

            records = []
            async for doc in cursor:
                records.append(doc)

            return records

        except Exception as e:
            logger.error(f"Failed to get session analytics: {str(e)}")
            raise

    async def get_room_analytics(
        self,
        room_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detection events for a room within a date range

        Args:
            room_id: Room identifier
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            List of detection records
        """
        try:
            query = {"room_id": room_id}

            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["detected_at"] = date_filter

            cursor = self.analytics_collection.find(query).sort("detected_at", -1)

            records = []
            async for doc in cursor:
                records.append(doc)

            return records

        except Exception as e:
            logger.error(f"Failed to get room analytics: {str(e)}")
            raise

    async def get_product_visibility_stats(
        self,
        room_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get product visibility statistics

        Args:
            room_id: Filter by room (optional)
            session_id: Filter by session (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)

        Returns:
            Statistics dictionary with product visibility data
        """
        try:
            # Build query
            match_query = {}
            if room_id:
                match_query["room_id"] = room_id
            if session_id:
                match_query["session_id"] = session_id
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_query["detected_at"] = date_filter

            # Aggregation pipeline
            pipeline = [
                {"$match": match_query},
                {
                    "$group": {
                        "_id": "$detected_class",
                        "total_detections": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"},
                        "total_duration": {"$sum": "$duration_seconds"},
                        "matched_products": {
                            "$addToSet": "$product_id"
                        }
                    }
                },
                {
                    "$project": {
                        "detected_class": "$_id",
                        "total_detections": 1,
                        "avg_confidence": 1,
                        "total_duration": 1,
                        "unique_products": {
                            "$size": {
                                "$filter": {
                                    "input": "$matched_products",
                                    "as": "item",
                                    "cond": {"$ne": ["$$item", None]}
                                }
                            }
                        }
                    }
                },
                {"$sort": {"total_detections": -1}}
            ]

            result = await self.analytics_collection.aggregate(pipeline).to_list(None)

            # Calculate summary
            total_detections = sum(r["total_detections"] for r in result)
            avg_confidence = (
                sum(r["avg_confidence"] * r["total_detections"] for r in result) / total_detections
                if total_detections > 0 else 0.0
            )

            return {
                "total_detections": total_detections,
                "avg_confidence": avg_confidence,
                "unique_classes": len(result),
                "by_class": result
            }

        except Exception as e:
            logger.error(f"Failed to get product visibility stats: {str(e)}")
            raise

    async def get_top_detected_products(
        self,
        room_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most frequently detected products

        Args:
            room_id: Filter by room (optional)
            limit: Number of top products to return

        Returns:
            List of top products with detection counts
        """
        try:
            match_query = {"product_id": {"$ne": None}}
            if room_id:
                match_query["room_id"] = room_id

            pipeline = [
                {"$match": match_query},
                {
                    "$group": {
                        "_id": "$product_id",
                        "total_detections": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"},
                        "total_duration": {"$sum": "$duration_seconds"},
                        "detected_class": {"$first": "$detected_class"}
                    }
                },
                {"$sort": {"total_detections": -1}},
                {"$limit": limit}
            ]

            result = await self.analytics_collection.aggregate(pipeline).to_list(limit)
            return result

        except Exception as e:
            logger.error(f"Failed to get top detected products: {str(e)}")
            raise

    async def cleanup_old_analytics(
        self,
        days_to_keep: int = 90
    ) -> int:
        """
        Clean up analytics data older than specified days

        Args:
            days_to_keep: Number of days to retain data

        Returns:
            Number of deleted documents
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            result = await self.analytics_collection.delete_many({
                "detected_at": {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old analytics records")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old analytics: {str(e)}")
            raise


def get_analytics_service(db: AsyncIOMotorDatabase) -> AnalyticsService:
    """Factory function to create analytics service instance"""
    return AnalyticsService(db)
