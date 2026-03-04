"""Livestream Session Service

Business logic for livestream session management operations.
"""

import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.livestream_session import (
    LivestreamSession,
    SessionStatus,
    SessionProduct,
    SessionStats
)
from app.schemas.livestream_session import (
    LivestreamSessionCreate,
    LivestreamSessionUpdate,
    SessionStatsUpdate
)


class LivestreamSessionService:
    """Service for livestream session management operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sessions_collection = db.livestream_sessions

    # CRUD Operations

    async def create_session(self, session_data: LivestreamSessionCreate) -> LivestreamSession:
        """Create a new livestream session"""
        # Convert products to SessionProduct objects
        products = [
            SessionProduct(**p.model_dump()) for p in session_data.products
        ]

        session = LivestreamSession(
            seller_id=session_data.seller_id,
            room_name=session_data.room_name,
            title=session_data.title,
            description=session_data.description,
            products=products,
            platforms=session_data.platforms,
            category=session_data.category,
            resolution=session_data.resolution,
            max_participants=session_data.max_participants,
            enable_agent=session_data.enable_agent,
            status=SessionStatus.PENDING
        )

        result = await self.sessions_collection.insert_one(
            session.model_dump(by_alias=True, exclude={"id"})
        )
        session.id = result.inserted_id
        return session

    async def get_session(self, session_id: str) -> Optional[LivestreamSession]:
        """Get a session by ID"""
        try:
            doc = await self.sessions_collection.find_one({"_id": ObjectId(session_id)})
            if doc:
                return LivestreamSession(**doc)
            return None
        except Exception:
            return None

    async def get_session_by_room_name(self, room_name: str) -> Optional[LivestreamSession]:
        """Get a session by room name"""
        doc = await self.sessions_collection.find_one({"room_name": room_name})
        if doc:
            return LivestreamSession(**doc)
        return None

    async def list_sessions(
        self,
        seller_id: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        platform: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[LivestreamSession], int]:
        """List sessions with filters"""
        query = {}

        if seller_id:
            query["seller_id"] = seller_id

        if status:
            query["status"] = status

        if category:
            # Filter by product category
            query["products.category"] = {"$regex": category, "$options": "i"}

        if platform:
            # Filter by platform stored in platforms array
            query["platforms"] = {"$regex": platform, "$options": "i"}

        # Get total count
        total = await self.sessions_collection.count_documents(query)

        # Get items
        cursor = self.sessions_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        items = []
        async for doc in cursor:
            items.append(LivestreamSession(**doc))

        return items, total

    async def update_session(
        self,
        session_id: str,
        update_data: LivestreamSessionUpdate
    ) -> Optional[LivestreamSession]:
        """Update a session"""
        session = await self.get_session(session_id)
        if not session:
            return None

        # Prepare update dict
        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle stats update separately
        if "stats" in update_dict and update_dict["stats"]:
            stats_update = update_dict.pop("stats")
            # Merge with existing stats
            current_stats = session.stats.model_dump()
            for key, value in stats_update.items():
                if value is not None:
                    current_stats[key] = value
            update_dict["stats"] = current_stats

        update_dict["updated_at"] = datetime.utcnow()

        # Perform update
        await self.sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_dict}
        )

        # Return updated session
        return await self.get_session(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        result = await self.sessions_collection.delete_one({"_id": ObjectId(session_id)})
        return result.deleted_count > 0

    # Status Transitions

    async def start_session(self, session_id: str) -> Optional[LivestreamSession]:
        """Start a livestream session (transition from pending to live)"""
        session = await self.get_session(session_id)
        if not session:
            return None

        if session.status != SessionStatus.PENDING:
            raise ValueError(f"Cannot start session with status '{session.status}'. Must be 'pending'.")

        await self.sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": SessionStatus.LIVE,
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return await self.get_session(session_id)

    async def end_session(
        self,
        session_id: str,
        stats_update: Optional[SessionStatsUpdate] = None
    ) -> Optional[LivestreamSession]:
        """End a livestream session (transition from live to ended)"""
        session = await self.get_session(session_id)
        if not session:
            return None

        if session.status not in (SessionStatus.LIVE, SessionStatus.PENDING):
            raise ValueError(f"Cannot end session with status '{session.status}'. Must be 'live' or 'pending'.")

        update_dict = {
            "status": SessionStatus.ENDED,
            "ended_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Update stats if provided
        if stats_update:
            current_stats = session.stats.model_dump()
            stats_data = stats_update.model_dump(exclude_unset=True)
            for key, value in stats_data.items():
                if value is not None:
                    current_stats[key] = value
            update_dict["stats"] = current_stats

        await self.sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_dict}
        )

        return await self.get_session(session_id)

    async def cancel_session(self, session_id: str) -> Optional[LivestreamSession]:
        """Cancel a session (only if pending)"""
        session = await self.get_session(session_id)
        if not session:
            return None

        if session.status != SessionStatus.PENDING:
            raise ValueError(f"Cannot cancel session with status '{session.status}'. Must be 'pending'.")

        await self.sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": SessionStatus.CANCELLED,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return await self.get_session(session_id)

    # Statistics

    async def update_stats(
        self,
        session_id: str,
        stats_update: SessionStatsUpdate
    ) -> Optional[LivestreamSession]:
        """Update session statistics"""
        session = await self.get_session(session_id)
        if not session:
            return None

        # Merge stats
        current_stats = session.stats.model_dump()
        stats_data = stats_update.model_dump(exclude_unset=True)
        for key, value in stats_data.items():
            if value is not None:
                current_stats[key] = value

        await self.sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "stats": current_stats,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return await self.get_session(session_id)

    async def get_seller_stats(self, seller_id: str) -> Dict:
        """Get aggregate statistics for a seller"""
        pipeline = [
            {"$match": {"seller_id": seller_id, "status": SessionStatus.ENDED}},
            {
                "$group": {
                    "_id": None,
                    "total_sessions": {"$sum": 1},
                    "total_revenue": {"$sum": "$stats.revenue"},
                    "total_products_sold": {"$sum": "$stats.products_sold"},
                    "total_viewers": {"$sum": "$stats.total_viewers"},
                    "avg_peak_viewers": {"$avg": "$stats.peak_viewers"}
                }
            }
        ]

        result = await self.sessions_collection.aggregate(pipeline).to_list(1)
        if result:
            stats = result[0]
            del stats["_id"]
            return stats

        return {
            "total_sessions": 0,
            "total_revenue": 0.0,
            "total_products_sold": 0,
            "total_viewers": 0,
            "avg_peak_viewers": 0.0
        }

    async def get_live_stats(self, session_id: str) -> Optional[Dict]:
        """Get real-time statistics for an active livestream session.

        Aggregates data from:
        - Session stats (viewers, messages, reactions)
        - Orders collection (order count and revenue)
        - Calculates conversion rate
        - Simulates hourly viewer data and channel performance
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        # Get order stats for this session
        orders_count = 0
        orders_revenue = 0.0
        try:
            orders_result = await self.db.orders.aggregate([
                {"$match": {"live_simulcast_id": session_id}},
                {
                    "$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "total": {"$sum": "$total_amount"}
                    }
                }
            ]).to_list(1)

            if orders_result:
                orders_count = orders_result[0].get("count", 0)
                orders_revenue = orders_result[0].get("total", 0.0)
        except Exception:
            # Orders collection might not exist or have different schema
            pass

        # Calculate conversion rate
        viewer_count = session.stats.total_viewers or session.stats.peak_viewers or 0
        conversion = (orders_count / viewer_count * 100) if viewer_count > 0 else 0.0

        # Generate hourly viewer data based on session duration
        hourly_viewers = []
        if session.started_at:
            start_hour = session.started_at.hour
            for i in range(4):
                hour = (start_hour + i) % 24
                # Simulate viewer pattern (ramp up then stabilize)
                peak = session.stats.peak_viewers or 100
                if i == 0:
                    viewers = int(peak * 0.6)
                elif i == 1:
                    viewers = peak
                elif i == 2:
                    viewers = int(peak * 0.85)
                else:
                    viewers = int(peak * 0.75)
                hourly_viewers.append({
                    "hour": f"{hour:02d}:00",
                    "viewers": viewers
                })
        else:
            # Default hourly data
            hourly_viewers = [
                {"hour": "12:00", "viewers": 0},
                {"hour": "13:00", "viewers": 0},
                {"hour": "14:00", "viewers": 0},
                {"hour": "15:00", "viewers": 0},
            ]

        # Simulate channel performance (split viewers across platforms)
        total_viewers = viewer_count
        channel_performance = [
            {
                "platform": "douyin",
                "platform_name": "Douyin",
                "viewers": int(total_viewers * 0.42)  # ~42% from Douyin
            },
            {
                "platform": "xiaohongshu",
                "platform_name": "Xiaohongshu",
                "viewers": int(total_viewers * 0.33)  # ~33% from Xiaohongshu
            },
            {
                "platform": "taobao",
                "platform_name": "Taobao",
                "viewers": int(total_viewers * 0.25)  # ~25% from Taobao
            }
        ]

        # Social stats from session
        social_stats = {
            "views": session.stats.total_viewers,
            "likes": session.stats.reaction_count,
            "comments": session.stats.message_count
        }

        return {
            "session_id": session_id,
            "orders": orders_count,
            "revenue": orders_revenue or session.stats.revenue,
            "conversion": round(conversion, 1),
            "viewer_count": viewer_count,
            "hourly_viewers": hourly_viewers,
            "channel_performance": channel_performance,
            "social_stats": social_stats
        }

    # Seeding

    async def seed_dummy_sessions(
        self, seller_id: str, count: int = 10
    ) -> List[LivestreamSession]:
        """Seed dummy ended sessions for history testing"""
        titles = [
            "Chic and Unique Tops on Sale!",
            "Matching Hat & Tops Collection",
            "Trimming Clothes for the Better",
            "Trending Office Pairs",
            "Summer Collection Preview",
            "Accessories Showcase",
            "Winter Coat Collection",
            "Beauty Essentials Live",
            "Home Decor Specials",
            "Weekend Flash Sale",
            "Designer Bags Showcase",
            "Fitness Gear Live",
        ]

        thumbnail_urls = [
            "https://images.unsplash.com/photo-1558171813-4c088753af8f?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1492707892479-7bc8d5a4ee93?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=300&fit=crop",
        ]

        dummy_products = [
            {
                "product_id": f"prod_{i}",
                "product_name": {"en": name, "ko": name},
                "sku": f"SKU-{1000 + i}",
                "unit_cost": round(random.uniform(20, 200), 2),
                "available_at_start": random.randint(20, 100),
                "category": random.choice(["Fashion", "Accessories", "Beauty", "Home"]),
                "image_url": f"https://picsum.photos/seed/{i}/200/200",
            }
            for i, name in enumerate(
                [
                    "Summer Dress",
                    "Designer Handbag",
                    "Skincare Set",
                    "Decorative Pillow",
                    "Smart Watch",
                    "Sunglasses",
                ]
            )
        ]

        sessions = []
        for i in range(count):
            days_ago = random.randint(1, 60)
            started_at = datetime.utcnow() - timedelta(days=days_ago)
            duration_minutes = random.randint(20, 120)
            ended_at = started_at + timedelta(minutes=duration_minutes)

            # Select random products
            num_products = random.randint(2, 5)
            selected_products = random.sample(
                dummy_products, min(num_products, len(dummy_products))
            )

            # Random platform combination
            all_platforms = ["Douyin", "Xiaohongshu", "Taobao Live", "SnapLive"]
            num_platforms = random.randint(2, 4)
            session_platforms = random.sample(all_platforms, num_platforms)

            session_category = random.choice(["Fashion", "Beauty", "Food", "Lifestyle", "Tech", "Shopping"])
            session_resolution = random.choice(["720p", "1080p", "4K"])

            session = LivestreamSession(
                seller_id=seller_id,
                room_name=f"session-{seller_id}-{int(started_at.timestamp())}",
                title=titles[i % len(titles)],
                description=f"Live session: {titles[i % len(titles)]}",
                thumbnail_url=thumbnail_urls[i % len(thumbnail_urls)],
                status=SessionStatus.ENDED,
                products=[SessionProduct(**p) for p in selected_products],
                platforms=session_platforms,
                category=session_category,
                resolution=session_resolution,
                max_participants=random.choice([100, 500, 1000]),
                enable_agent=random.choice([True, False]),
                started_at=started_at,
                ended_at=ended_at,
                stats=SessionStats(
                    peak_viewers=random.randint(50, 500),
                    total_viewers=random.randint(100, 3000),
                    products_sold=random.randint(5, 100),
                    revenue=round(random.uniform(500, 10000), 2),
                    message_count=random.randint(50, 500),
                    reaction_count=random.randint(100, 2000),
                    average_watch_time_seconds=random.randint(60, 600),
                ),
            )

            result = await self.sessions_collection.insert_one(
                session.model_dump(by_alias=True, exclude={"id"})
            )
            session.id = result.inserted_id
            sessions.append(session)

        return sessions
