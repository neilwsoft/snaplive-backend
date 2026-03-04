"""Platform Service

Business logic for managing platform store connections, credentials, and platform information.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.platform_store import (
    PlatformStore,
    Platform,
    ConnectionStatus,
    SyncStatus,
    PlatformStoreConfig,
)
from app.models.platform_credential import PlatformCredential, CredentialType
from app.adapters import (
    TaobaoMockAdapter,
    DouyinMockAdapter,
    XiaohongshuMockAdapter,
)


class PlatformService:
    """Service for platform and store connection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.stores_collection = db.platform_stores
        self.credentials_collection = db.platform_credentials
        self.sellers_collection = db.sellers

    def _get_adapter(self, platform: Platform, credentials: Dict[str, str]):
        """Get the appropriate adapter for a platform"""
        if platform == Platform.TAOBAO:
            return TaobaoMockAdapter(credentials)
        elif platform == Platform.DOUYIN:
            return DouyinMockAdapter(credentials)
        elif platform == Platform.XIAOHONGSHU:
            return XiaohongshuMockAdapter(credentials)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def get_platform_info(self, platform: Platform) -> Dict[str, Any]:
        """Get information about a specific platform"""
        platform_info = {
            Platform.TAOBAO: {
                "platform": "taobao",
                "display_name": "Taobao Live",
                "description": "China's largest C2C e-commerce platform with live streaming",
                "logo_url": "/images/platforms/taobao.png",
                "is_available": True,
                "requires_oauth": False,
                "supports_rtmp": True,
                "supports_inventory_sync": True,
                "supports_order_sync": True,
                "supports_product_sync": True,
                "supports_stream_data": True,
                "required_fields": ["app_key", "app_secret", "session_key"],
                "optional_fields": ["store_url"],
                "rate_limit_per_minute": 10000,
                "documentation_url": "https://open.taobao.com",
                "setup_guide_url": "https://open.taobao.com/doc.htm",
            },
            Platform.DOUYIN: {
                "platform": "douyin",
                "display_name": "Douyin (抖音)",
                "description": "China's leading short video and live streaming platform",
                "logo_url": "/images/platforms/douyin.png",
                "is_available": True,
                "requires_oauth": True,
                "supports_rtmp": True,
                "supports_inventory_sync": True,
                "supports_order_sync": True,
                "supports_product_sync": True,
                "supports_stream_data": True,
                "required_fields": ["client_key", "client_secret"],
                "optional_fields": ["access_token", "refresh_token"],
                "rate_limit_per_minute": 5000,
                "documentation_url": "https://open.douyin.com",
                "setup_guide_url": "https://open.douyin.com/platform/doc",
            },
            Platform.XIAOHONGSHU: {
                "platform": "xiaohongshu",
                "display_name": "Xiaohongshu (小红书)",
                "description": "China's lifestyle and shopping community platform",
                "logo_url": "/images/platforms/xiaohongshu.png",
                "is_available": True,
                "requires_oauth": False,
                "supports_rtmp": True,
                "supports_inventory_sync": True,
                "supports_order_sync": True,
                "supports_product_sync": True,
                "supports_stream_data": True,
                "required_fields": ["app_id", "app_secret"],
                "optional_fields": ["store_url"],
                "rate_limit_per_minute": 3000,
                "documentation_url": "https://school.xiaohongshu.com",
                "setup_guide_url": "https://school.xiaohongshu.com/docs",
            },
        }

        return platform_info.get(platform, {})

    async def list_platforms(self) -> List[Dict[str, Any]]:
        """List all available platforms"""
        platforms = [
            await self.get_platform_info(Platform.TAOBAO),
            await self.get_platform_info(Platform.DOUYIN),
            await self.get_platform_info(Platform.XIAOHONGSHU),
        ]
        return platforms

    async def create_store_connection(
        self,
        seller_id: str,
        platform: Platform,
        store_id: str,
        store_name: str,
        credentials: Dict[str, str],
        store_url: Optional[str] = None,
        config: Optional[PlatformStoreConfig] = None,
    ) -> Dict[str, Any]:
        """Create a new platform store connection"""

        # Test connection first
        adapter = self._get_adapter(platform, credentials)
        connection_test = await adapter.test_connection()

        if not connection_test["success"]:
            return {
                "success": False,
                "message": connection_test["message"],
                "store_id": None,
            }

        # Get store info from platform
        store_info = await adapter.get_store_info(store_id)

        # Convert seller_id to ObjectId (create new one if invalid)
        if ObjectId.is_valid(seller_id):
            seller_object_id = ObjectId(seller_id)
        else:
            # For demo/invalid IDs, create a new ObjectId
            seller_object_id = ObjectId()

        # Create credential record
        credential_data = {
            "seller_id": seller_object_id,
            "platform": platform.value,
            "credential_type": CredentialType.API_KEY.value,
            **{k: v for k, v in credentials.items() if v},
            "is_valid": True,
            "last_validated_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        credential_result = await self.credentials_collection.insert_one(credential_data)
        credential_id = credential_result.inserted_id

        # Create store connection record
        store_data = {
            "seller_id": seller_object_id,
            "platform": platform.value,
            "store_id": store_id,
            "store_name": store_name or store_info.get("store_name", f"{platform.value} Store"),
            "store_url": store_url or store_info.get("store_url"),
            "connection_status": ConnectionStatus.CONNECTED.value,
            "last_sync_status": SyncStatus.IDLE.value,
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "config": (config.dict() if config else PlatformStoreConfig().dict()),
            "credential_id": credential_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "connected_at": datetime.utcnow(),
        }
        store_result = await self.stores_collection.insert_one(store_data)

        return {
            "success": True,
            "message": f"Successfully connected to {platform.value}",
            "store_id": str(store_result.inserted_id),
            "store_info": store_info,
        }

    async def get_store(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Get a store by ID"""
        store = await self.stores_collection.find_one({"_id": ObjectId(store_id)})
        if store:
            store["id"] = str(store.pop("_id"))
            store["seller_id"] = str(store["seller_id"])
            if store.get("credential_id"):
                store["credential_id"] = str(store["credential_id"])
        return store

    async def list_stores(
        self,
        seller_id: Optional[str] = None,
        platform: Optional[Platform] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """List stores with optional filters"""
        query = {}
        if seller_id:
            # Check if seller_id is a valid ObjectId
            if ObjectId.is_valid(seller_id):
                query["seller_id"] = ObjectId(seller_id)
            else:
                # If not valid ObjectId, return empty result
                return {
                    "stores": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                }
        if platform:
            query["platform"] = platform.value

        total = await self.stores_collection.count_documents(query)

        cursor = self.stores_collection.find(query).skip((page - 1) * page_size).limit(page_size)
        stores = await cursor.to_list(length=page_size)

        # Convert ObjectIds to strings and rename _id to id
        for store in stores:
            store["id"] = str(store.pop("_id"))
            store["seller_id"] = str(store["seller_id"])
            if store.get("credential_id"):
                store["credential_id"] = str(store["credential_id"])

        return {
            "stores": stores,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def update_store(
        self,
        store_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a store connection"""
        updates["updated_at"] = datetime.utcnow()

        result = await self.stores_collection.update_one(
            {"_id": ObjectId(store_id)},
            {"$set": updates}
        )

        if result.modified_count > 0:
            return {"success": True, "message": "Store updated successfully"}
        else:
            return {"success": False, "message": "Store not found or no changes made"}

    async def delete_store(self, store_id: str) -> Dict[str, Any]:
        """Delete a store connection"""
        store = await self.get_store(store_id)
        if not store:
            return {"success": False, "message": "Store not found"}

        # Delete associated credential
        if store.get("credential_id"):
            await self.credentials_collection.delete_one(
                {"_id": ObjectId(store["credential_id"])}
            )

        # Delete store
        await self.stores_collection.delete_one({"_id": ObjectId(store_id)})

        return {"success": True, "message": "Store connection deleted successfully"}

    async def test_store_connection(self, store_id: str) -> Dict[str, Any]:
        """Test a store's connection to its platform"""
        store = await self.get_store(store_id)
        if not store:
            return {"success": False, "message": "Store not found"}

        # Get credentials
        credential = await self.credentials_collection.find_one(
            {"_id": ObjectId(store["credential_id"])}
        )
        if not credential:
            return {"success": False, "message": "Credentials not found"}

        # Extract credentials dict
        creds = {
            k: v for k, v in credential.items()
            if k in ["api_key", "api_secret", "app_key", "session_key", "access_token",
                     "refresh_token", "client_key", "client_secret", "app_id"] and v
        }

        # Test connection
        adapter = self._get_adapter(Platform(store["platform"]), creds)
        result = await adapter.test_connection()

        # Update store status
        if result["success"]:
            await self.update_store(store_id, {
                "connection_status": ConnectionStatus.CONNECTED.value,
                "connection_error": None,
            })
        else:
            await self.update_store(store_id, {
                "connection_status": ConnectionStatus.ERROR.value,
                "connection_error": result.get("message"),
            })

        return {
            **result,
            "tested_at": datetime.utcnow(),
        }

    async def get_store_with_adapter(self, store_id: str):
        """Get store and its initialized adapter"""
        store = await self.get_store(store_id)
        if not store:
            return None, None

        credential = await self.credentials_collection.find_one(
            {"_id": ObjectId(store["credential_id"])}
        )
        if not credential:
            return store, None

        creds = {
            k: v for k, v in credential.items()
            if k in ["api_key", "api_secret", "app_key", "session_key", "access_token",
                     "refresh_token", "client_key", "client_secret", "app_id"] and v
        }

        adapter = self._get_adapter(Platform(store["platform"]), creds)
        return store, adapter
