"""Simulcaster Service

Business logic for simulcaster operations including leaderboard/ranking.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


def _to_str(value) -> Optional[str]:
    """Convert a value to string, handling datetime objects from MongoDB."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class SimulcasterService:
    """Service for simulcaster operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sessions_collection = db.livestream_sessions
        self.users_collection = db.users

    async def get_top_simulcasters(
        self,
        time_period: Optional[str] = "all_time",
        category: Optional[str] = None,
        marketplace: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[dict], int]:
        """
        Get top simulcasters ranked by total views

        Args:
            time_period: "all_time", "month", or "week"
            category: Filter by product category
            marketplace: Filter by platform
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of top simulcasters, total count)
        """
        # Build match filter
        match_filter = {"status": {"$in": ["live", "ended"]}}

        # Time period filter
        if time_period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
            match_filter["created_at"] = {"$gte": start_date.isoformat()}
        elif time_period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
            match_filter["created_at"] = {"$gte": start_date.isoformat()}

        # Category filter (check if any product in session has the category)
        if category:
            match_filter["products.category"] = category

        # Platform filter would require platform tracking in sessions
        # For now, skip this filter as it's not in the current session schema

        # Aggregation pipeline
        pipeline = [
            {"$match": match_filter},
            # Group by seller_id and aggregate stats
            {
                "$group": {
                    "_id": "$seller_id",
                    "total_views": {"$sum": "$stats.total_viewers"},
                    "total_likes": {"$sum": "$stats.reaction_count"},
                    "total_comments": {"$sum": "$stats.message_count"},
                    "session_count": {"$sum": 1},
                    # Collect unique categories
                    "categories": {"$addToSet": "$products.category"},
                }
            },
            # Sort by total views descending
            {"$sort": {"total_views": -1}},
        ]

        # Execute aggregation
        aggregated_data = await self.sessions_collection.aggregate(pipeline).to_list(None)

        total_count = len(aggregated_data)

        # Apply pagination
        paginated_data = aggregated_data[skip : skip + limit]

        # Enrich with user data and add rank
        enriched_data = []
        for idx, item in enumerate(paginated_data):
            seller_id = item["_id"]

            # Fetch user data
            user = await self.users_collection.find_one({"_id": ObjectId(seller_id)})

            # Flatten categories (they're nested arrays from addToSet on array field)
            categories = []
            if item.get("categories"):
                for cat_list in item["categories"]:
                    if isinstance(cat_list, list):
                        categories.extend(cat_list)
                    elif cat_list:
                        categories.append(cat_list)
            # Remove duplicates and None values
            categories = list(set(filter(None, categories)))

            enriched_item = {
                "seller_id": seller_id,
                "rank": skip + idx + 1,  # Calculate rank based on position
                "name": user.get("full_name", "Unknown") if user else "Unknown",
                "avatar_url": user.get("avatar_url") if user else None,
                "verified": user.get("verified", False) if user else False,
                "platforms": [],  # TODO: Track platforms in sessions
                "total_views": item.get("total_views", 0),
                "total_likes": item.get("total_likes", 0),
                "total_comments": item.get("total_comments", 0),
                "categories": categories,
                "session_count": item.get("session_count", 0),
            }

            enriched_data.append(enriched_item)

        return enriched_data, total_count

    async def get_seller_profile(
        self,
        seller_id: str,
        recent_sessions_limit: int = 10,
    ) -> Optional[dict]:
        """
        Get a seller's profile with aggregated stats and recent sessions.

        Args:
            seller_id: The seller's user ID
            recent_sessions_limit: Max recent sessions to return

        Returns:
            Seller profile dict or None if user not found
        """
        # Fetch user
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(seller_id)})
        except Exception:
            return None

        if not user:
            return None

        # Aggregate stats from sessions
        stats_pipeline = [
            {"$match": {"seller_id": seller_id, "status": {"$in": ["live", "ended"]}}},
            {
                "$group": {
                    "_id": "$seller_id",
                    "total_views": {"$sum": "$stats.total_viewers"},
                    "total_likes": {"$sum": "$stats.reaction_count"},
                    "total_comments": {"$sum": "$stats.message_count"},
                    "session_count": {"$sum": 1},
                    "categories": {"$addToSet": "$products.category"},
                }
            },
        ]

        stats_results = await self.sessions_collection.aggregate(stats_pipeline).to_list(None)
        stats = stats_results[0] if stats_results else {}

        # Flatten categories
        categories = []
        if stats.get("categories"):
            for cat_list in stats["categories"]:
                if isinstance(cat_list, list):
                    categories.extend(cat_list)
                elif cat_list:
                    categories.append(cat_list)
        categories = list(set(filter(None, categories)))

        # Aggregate unique platforms from sessions
        platforms_pipeline = [
            {"$match": {"seller_id": seller_id, "status": {"$in": ["live", "ended"]}}},
            {"$unwind": {"path": "$platforms", "preserveNullAndEmptyArrays": False}},
            {"$group": {"_id": None, "platforms": {"$addToSet": "$platforms"}}},
        ]
        platforms_results = await self.sessions_collection.aggregate(platforms_pipeline).to_list(None)
        platforms = platforms_results[0]["platforms"] if platforms_results else []

        # Fetch recent sessions
        recent_sessions_cursor = self.sessions_collection.find(
            {"seller_id": seller_id}
        ).sort("created_at", -1).limit(recent_sessions_limit)

        recent_sessions = []
        async for session in recent_sessions_cursor:
            session_stats = session.get("stats", {})
            recent_sessions.append({
                "session_id": str(session["_id"]),
                "title": session.get("title"),
                "status": session.get("status", "unknown"),
                "created_at": _to_str(session.get("created_at")),
                "started_at": _to_str(session.get("started_at")),
                "ended_at": _to_str(session.get("ended_at")),
                "duration_seconds": session_stats.get("duration_seconds"),
                "total_viewers": session_stats.get("total_viewers", 0),
                "revenue": session_stats.get("revenue", 0.0),
                "platforms": session.get("platforms", []),
                "category": session.get("products", [{}])[0].get("category") if session.get("products") else None,
            })

        member_since = _to_str(user.get("created_at"))

        return {
            "seller_id": seller_id,
            "name": user.get("full_name", "Unknown"),
            "avatar_url": user.get("avatar_url"),
            "verified": user.get("verified", False),
            "member_since": member_since,
            "platforms": platforms,
            "total_views": stats.get("total_views", 0),
            "total_likes": stats.get("total_likes", 0),
            "total_comments": stats.get("total_comments", 0),
            "categories": categories,
            "session_count": stats.get("session_count", 0),
            "recent_sessions": recent_sessions,
        }
