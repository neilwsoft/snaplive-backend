"""Simulcaster Service

Business logic for simulcaster operations including leaderboard/ranking.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


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
