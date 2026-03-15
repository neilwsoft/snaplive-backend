"""Platform Stats Service

Aggregates stats from multiple collections for the platform overview.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase


class PlatformStatsService:
    """Service for aggregating platform-wide statistics"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_stats(self) -> dict:
        """Get aggregated platform statistics from multiple collections"""
        live_task = self._get_live_stats()
        users_task = self._get_total_users()
        platforms_task = self._get_marketplace_platforms()

        live_stats, total_users, marketplace_platforms = await asyncio.gather(
            live_task, users_task, platforms_task
        )

        return {
            "live_sessions": live_stats["count"],
            "active_viewers": live_stats["viewers"],
            "total_users": total_users,
            "marketplace_platforms": marketplace_platforms,
        }

    async def _get_live_stats(self) -> dict:
        """Count live sessions and sum their peak viewers"""
        pipeline = [
            {"$match": {"status": "live"}},
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "viewers": {"$sum": "$stats.peak_viewers"},
                }
            },
        ]
        result = await self.db.livestream_sessions.aggregate(pipeline).to_list(1)
        if result:
            return {"count": result[0]["count"], "viewers": result[0]["viewers"]}
        return {"count": 0, "viewers": 0}

    async def _get_total_users(self) -> int:
        """Count all users"""
        return await self.db.users.count_documents({})

    async def _get_marketplace_platforms(self) -> int:
        """Count connected platform stores"""
        return await self.db.platform_stores.count_documents(
            {"connection_status": "connected"}
        )
