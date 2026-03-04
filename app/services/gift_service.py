"""Gift Service

Business logic for virtual gift management operations.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.gift import Gift, MarketplaceSource, TierLevel
from app.schemas.gift import GiftCreate, GiftUpdate


class GiftService:
    """Service for gift management operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.gifts

    async def create_gift(self, gift_data: GiftCreate) -> Gift:
        """Create a new gift record"""
        gift = Gift(
            raw_gift_name=gift_data.raw_gift_name,
            image_url=gift_data.image_url,
            quantity=gift_data.quantity,
            marketplace_source=gift_data.marketplace_source,
            live_simulcast_id=gift_data.live_simulcast_id,
            viewer_username=gift_data.viewer_username,
            viewer_avatar_url=gift_data.viewer_avatar_url,
            gifting_timestamp=gift_data.gifting_timestamp or datetime.utcnow(),
            virtual_currency_value=gift_data.virtual_currency_value,
            currency_label=gift_data.currency_label,
            tier_level=gift_data.tier_level,
            seller_id=gift_data.seller_id,
        )

        result = await self.collection.insert_one(
            gift.model_dump(by_alias=True, exclude={"id"})
        )
        gift.id = result.inserted_id
        return gift

    async def get_gift(self, gift_id: str) -> Optional[Gift]:
        """Get a gift by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(gift_id)})
            if doc:
                return Gift(**doc)
            return None
        except Exception:
            return None

    async def get_gifts(
        self,
        marketplace_source: Optional[str] = None,
        tier_level: Optional[str] = None,
        live_simulcast_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Gift], int]:
        """List gifts with filtering and pagination"""
        query = {}

        if marketplace_source:
            query["marketplace_source"] = marketplace_source

        if tier_level:
            query["tier_level"] = tier_level

        if live_simulcast_id:
            query["live_simulcast_id"] = live_simulcast_id

        if search:
            query["$or"] = [
                {"raw_gift_name": {"$regex": search, "$options": "i"}},
                {"viewer_username": {"$regex": search, "$options": "i"}},
                {"live_simulcast_id": {"$regex": search, "$options": "i"}},
            ]

        total = await self.collection.count_documents(query)
        skip = (page - 1) * page_size

        cursor = (
            self.collection.find(query)
            .sort("gifting_timestamp", -1)
            .skip(skip)
            .limit(page_size)
        )

        items = []
        async for doc in cursor:
            items.append(Gift(**doc))

        return items, total

    async def update_gift(
        self, gift_id: str, update_data: GiftUpdate
    ) -> Optional[Gift]:
        """Update a gift"""
        gift = await self.get_gift(gift_id)
        if not gift:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(gift_id)},
            {"$set": update_dict},
        )

        return await self.get_gift(gift_id)

    async def delete_gift(self, gift_id: str) -> bool:
        """Delete a gift"""
        result = await self.collection.delete_one({"_id": ObjectId(gift_id)})
        return result.deleted_count > 0

    async def get_gift_stats(self) -> dict:
        """Get gift statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_gifts": {"$sum": 1},
                    "total_quantity": {"$sum": "$quantity"},
                    "total_value": {"$sum": {"$multiply": ["$virtual_currency_value", "$quantity"]}},
                }
            }
        ]
        result = await self.collection.aggregate(pipeline).to_list(1)

        if result:
            stats = result[0]
            del stats["_id"]
            return stats

        return {
            "total_gifts": 0,
            "total_quantity": 0,
            "total_value": 0.0,
        }

    async def seed_gifts(self, count: int = 24) -> List[Gift]:
        """Seed the database with realistic gift data"""
        # Clear existing gifts
        await self.collection.delete_many({})

        # Realistic gift data matching the screenshot
        gift_templates = [
            {
                "raw_gift_name": "Tiktok Universe (抖音宇宙)",
                "image_url": "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?w=100&h=100&fit=crop",
                "marketplace_source": "douyin",
                "virtual_currency_value": 3000,
                "currency_label": "Douyin",
                "tier_level": "large",
            },
            {
                "raw_gift_name": "Sports Car (跑车)",
                "image_url": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=100&h=100&fit=crop",
                "marketplace_source": "douyin",
                "virtual_currency_value": 990,
                "currency_label": "Douyin",
                "tier_level": "large",
            },
            {
                "raw_gift_name": "Carnival Castle (狂欢城堡)",
                "image_url": "https://images.unsplash.com/photo-1562654501-a0ccc0fc3fb1?w=100&h=100&fit=crop",
                "marketplace_source": "taobao",
                "virtual_currency_value": 19900,
                "currency_label": "Taobao",
                "tier_level": "large",
            },
            {
                "raw_gift_name": "Little Red Balloon (小红气球)",
                "image_url": "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=100&h=100&fit=crop",
                "marketplace_source": "xiaohongshu",
                "virtual_currency_value": 5,
                "currency_label": "Red Note",
                "tier_level": "small",
            },
            {
                "raw_gift_name": "Diamond (钻石)",
                "image_url": "https://images.unsplash.com/photo-1573408301185-9146fe634ad0?w=100&h=100&fit=crop",
                "marketplace_source": "snaplive",
                "virtual_currency_value": 100,
                "currency_label": "Snap",
                "tier_level": "large",
            },
            {
                "raw_gift_name": "Lion (狮子)",
                "image_url": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=100&h=100&fit=crop",
                "marketplace_source": "douyin",
                "virtual_currency_value": 29500,
                "currency_label": "Douyin",
                "tier_level": "premium",
            },
            {
                "raw_gift_name": "Heart (爱心)",
                "image_url": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=100&h=100&fit=crop",
                "marketplace_source": "taobao",
                "virtual_currency_value": 1,
                "currency_label": "Taobao",
                "tier_level": "small",
            },
            {
                "raw_gift_name": "Rose (玫瑰)",
                "image_url": "https://images.unsplash.com/photo-1490750967868-88aa4f44baee?w=100&h=100&fit=crop",
                "marketplace_source": "douyin",
                "virtual_currency_value": 50,
                "currency_label": "Douyin",
                "tier_level": "medium",
            },
            {
                "raw_gift_name": "Thank You Note (感谢卡)",
                "image_url": "https://images.unsplash.com/photo-1606567595334-d39972c85dbe?w=100&h=100&fit=crop",
                "marketplace_source": "snaplive",
                "virtual_currency_value": 10,
                "currency_label": "Snap",
                "tier_level": "small",
            },
            {
                "raw_gift_name": "Fortune Airship (财富飞艇)",
                "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop",
                "marketplace_source": "taobao",
                "virtual_currency_value": 4980,
                "currency_label": "Taobao",
                "tier_level": "large",
            },
            {
                "raw_gift_name": "Love Paper Crane (爱心纸鹤)",
                "image_url": "https://images.unsplash.com/photo-1582845512747-e42001c95638?w=100&h=100&fit=crop",
                "marketplace_source": "douyin",
                "virtual_currency_value": 20,
                "currency_label": "Douyin",
                "tier_level": "medium",
            },
            {
                "raw_gift_name": "Galaxy Rocket (银河火箭)",
                "image_url": "https://images.unsplash.com/photo-1457364559154-aa2644600ebb?w=100&h=100&fit=crop",
                "marketplace_source": "snaplive",
                "virtual_currency_value": 500,
                "currency_label": "Snap",
                "tier_level": "premium",
            },
            {
                "raw_gift_name": "Fireworks (烟花)",
                "image_url": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=100&h=100&fit=crop",
                "marketplace_source": "xiaohongshu",
                "virtual_currency_value": 99,
                "currency_label": "Red Note",
                "tier_level": "medium",
            },
            {
                "raw_gift_name": "Golden Crown (金冠)",
                "image_url": "https://images.unsplash.com/photo-1589656966895-2f33e7653571?w=100&h=100&fit=crop",
                "marketplace_source": "douyin",
                "virtual_currency_value": 10000,
                "currency_label": "Douyin",
                "tier_level": "premium",
            },
            {
                "raw_gift_name": "Star Wand (星光棒)",
                "image_url": "https://images.unsplash.com/photo-1519750157634-b6d493a0f77c?w=100&h=100&fit=crop",
                "marketplace_source": "taobao",
                "virtual_currency_value": 520,
                "currency_label": "Taobao",
                "tier_level": "large",
            },
            {
                "raw_gift_name": "Lucky Cat (招财猫)",
                "image_url": "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=100&h=100&fit=crop",
                "marketplace_source": "xiaohongshu",
                "virtual_currency_value": 66,
                "currency_label": "Red Note",
                "tier_level": "medium",
            },
        ]

        # Viewer data
        viewers = [
            {"username": "Best Price Ben 好价", "avatar": None},
            {"username": "Sincere Sarah 心心", "avatar": None},
            {"username": "Click King 点点", "avatar": None},
            {"username": "Easy Pick 易选", "avatar": None},
            {"username": "Annie 安安", "avatar": None},
            {"username": "Rapid Rob 罗博", "avatar": None},
            {"username": "Best Price Ben 好价", "avatar": None},
            {"username": "Lucky Liu 刘幸", "avatar": None},
        ]

        simulcast_ids = [
            "LIVE-7B8D-A2C4-F0E3",
            "LIVE-3F1A-B9D7-E5C2",
            "LIVE-8E4C-D6A1-F7B9",
        ]

        gifts = []
        for i in range(count):
            template = gift_templates[i % len(gift_templates)]
            viewer = random.choice(viewers)
            simulcast_id = random.choice(simulcast_ids)

            # Randomize quantity (most are x1, some higher)
            qty = 1
            if random.random() < 0.15:
                qty = random.choice([5, 10, 50, 100])

            # Spread timestamps across last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)

            gift = Gift(
                raw_gift_name=template["raw_gift_name"],
                image_url=template["image_url"],
                quantity=qty,
                marketplace_source=template["marketplace_source"],
                live_simulcast_id=simulcast_id,
                viewer_username=viewer["username"],
                viewer_avatar_url=viewer["avatar"],
                gifting_timestamp=timestamp,
                virtual_currency_value=template["virtual_currency_value"],
                currency_label=template["currency_label"],
                tier_level=template["tier_level"],
                created_at=timestamp,
                updated_at=timestamp,
            )

            result = await self.collection.insert_one(
                gift.model_dump(by_alias=True, exclude={"id"})
            )
            gift.id = result.inserted_id
            gifts.append(gift)

        return gifts
