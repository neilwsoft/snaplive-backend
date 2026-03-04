"""Simulcast Preset Service

Business logic for simulcast preset CRUD operations.
"""

import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.simulcast_preset import (
    SimulcastPreset,
    PlatformConfig,
    PresetProduct,
    CameraConfig,
    BrandingConfig,
)
from app.schemas.simulcast_preset import (
    SimulcastPresetCreate,
    SimulcastPresetUpdate,
)


class SimulcastPresetService:
    """Service for managing simulcast presets"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.simulcast_presets

    async def create_preset(self, data: SimulcastPresetCreate) -> SimulcastPreset:
        """Create a new simulcast preset"""
        preset = SimulcastPreset(
            seller_id=data.seller_id,
            title=data.title,
            description=data.description,
            resolution=data.resolution,
            platforms=[PlatformConfig(**p.model_dump()) for p in data.platforms],
            products=[PresetProduct(**p.model_dump()) for p in data.products],
            invited_user_ids=data.invited_user_ids,
            cameras=[CameraConfig(**c.model_dump()) for c in data.cameras],
            branding=BrandingConfig(**data.branding.model_dump()),
        )

        result = await self.collection.insert_one(
            preset.model_dump(by_alias=True, exclude={"id"})
        )
        preset.id = result.inserted_id
        return preset

    async def get_preset(self, preset_id: str) -> Optional[SimulcastPreset]:
        """Get a preset by ID"""
        if not ObjectId.is_valid(preset_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(preset_id)})
        if doc:
            return SimulcastPreset(**doc)
        return None

    async def list_presets(
        self,
        seller_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[SimulcastPreset], int]:
        """List presets with optional filtering and pagination"""
        query = {}
        if seller_id:
            query["seller_id"] = seller_id

        total = await self.collection.count_documents(query)

        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        presets = []
        async for doc in cursor:
            presets.append(SimulcastPreset(**doc))

        return presets, total

    async def update_preset(
        self, preset_id: str, data: SimulcastPresetUpdate
    ) -> Optional[SimulcastPreset]:
        """Update a preset"""
        if not ObjectId.is_valid(preset_id):
            return None

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_preset(preset_id)

        # Convert nested objects
        if "platforms" in update_data and update_data["platforms"] is not None:
            update_data["platforms"] = [
                PlatformConfig(**p).model_dump() for p in update_data["platforms"]
            ]
        if "products" in update_data and update_data["products"] is not None:
            update_data["products"] = [
                PresetProduct(**p).model_dump() for p in update_data["products"]
            ]
        if "cameras" in update_data and update_data["cameras"] is not None:
            update_data["cameras"] = [
                CameraConfig(**c).model_dump() for c in update_data["cameras"]
            ]
        if "branding" in update_data and update_data["branding"] is not None:
            update_data["branding"] = BrandingConfig(
                **update_data["branding"]
            ).model_dump()

        update_data["updated_at"] = datetime.utcnow()

        await self.collection.update_one(
            {"_id": ObjectId(preset_id)}, {"$set": update_data}
        )

        return await self.get_preset(preset_id)

    async def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset"""
        if not ObjectId.is_valid(preset_id):
            return False

        result = await self.collection.delete_one({"_id": ObjectId(preset_id)})
        return result.deleted_count > 0

    async def increment_use_count(self, preset_id: str) -> Optional[SimulcastPreset]:
        """Increment the use count and update last_used_at"""
        if not ObjectId.is_valid(preset_id):
            return None

        await self.collection.update_one(
            {"_id": ObjectId(preset_id)},
            {
                "$inc": {"use_count": 1},
                "$set": {
                    "last_used_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            },
        )

        return await self.get_preset(preset_id)

    async def seed_dummy_presets(
        self, seller_id: str, count: int = 5
    ) -> List[SimulcastPreset]:
        """Generate dummy presets for testing"""
        titles = [
            "Summer Collection Live",
            "Flash Sale Friday",
            "New Arrivals Showcase",
            "Weekend Special",
            "Holiday Gift Guide",
            "Morning Show Setup",
            "Evening Prime Time",
            "Fashion Week Special",
            "Beauty Essentials",
            "Home Decor Live",
        ]

        resolutions = ["Auto", "4K", "1080p", "720p"]

        dummy_products = [
            {
                "product_id": f"prod_{i}",
                "name": name,
                "image_url": f"https://picsum.photos/seed/{i}/200/200",
                "sku": f"SKU-{1000 + i}",
                "quantity": random.randint(10, 100),
                "unit_cost": round(random.uniform(10, 500), 2),
                "category": random.choice(["Fashion", "Electronics", "Home", "Beauty"]),
            }
            for i, name in enumerate(
                [
                    "Stylish Summer Dress",
                    "Wireless Earbuds",
                    "Decorative Pillow",
                    "Skincare Set",
                    "Designer Handbag",
                    "Smart Watch",
                    "Cozy Blanket",
                    "Makeup Palette",
                ]
            )
        ]

        presets = []
        for i in range(count):
            # Select random products
            num_products = random.randint(2, 5)
            selected_products = random.sample(
                dummy_products, min(num_products, len(dummy_products))
            )

            preset_data = SimulcastPresetCreate(
                seller_id=seller_id,
                title=titles[i % len(titles)],
                description=f"Preset configuration for {titles[i % len(titles)]}",
                resolution=random.choice(resolutions),
                platforms=[
                    {"name": "Douyin", "connected": True, "signal_strength": random.randint(3, 5)},
                    {"name": "Xiaohongshu", "connected": True, "signal_strength": random.randint(2, 5)},
                    {"name": "Taobao Live", "connected": random.choice([True, False]), "signal_strength": random.randint(0, 5)},
                ],
                products=selected_products,
                invited_user_ids=[f"user_{j}" for j in range(random.randint(0, 3))],
                cameras=[
                    {"camera_id": "cam_1", "name": "Main Camera", "selected": True, "preview_url": None},
                    {"camera_id": "cam_2", "name": "Side Camera", "selected": random.choice([True, False]), "preview_url": None},
                ],
                branding={
                    "landscape_logo_url": None,
                    "boxed_logo_url": None,
                },
            )

            preset = await self.create_preset(preset_data)

            # Randomly set some as used
            if random.choice([True, False]):
                days_ago = random.randint(1, 30)
                await self.collection.update_one(
                    {"_id": preset.id},
                    {
                        "$set": {
                            "use_count": random.randint(1, 10),
                            "last_used_at": datetime.utcnow() - timedelta(days=days_ago),
                        }
                    },
                )
                preset = await self.get_preset(str(preset.id))

            presets.append(preset)

        return presets
