"""Sync Service

Business logic for synchronizing data between SnapLive and platform stores.
Handles inventory, orders, products, and stream data synchronization.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.sync_log import (
    SyncLog,
    SyncType,
    SyncStatus,
    SyncDirection,
    SyncResult,
    Platform,
)
from app.services.platform_service import PlatformService


class SyncService:
    """Service for data synchronization operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sync_logs_collection = db.sync_logs
        self.stores_collection = db.platform_stores
        self.orders_collection = db.orders
        self.inventory_collection = db.inventory
        self.products_collection = db.products
        self.platform_service = PlatformService(db)

    async def trigger_sync(
        self,
        store_id: str,
        sync_type: SyncType,
        sync_direction: SyncDirection = SyncDirection.PULL,
        triggered_by: str = "manual",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger a synchronization operation"""

        # Get store and adapter
        store, adapter = await self.platform_service.get_store_with_adapter(store_id)
        if not store or not adapter:
            return {
                "success": False,
                "message": "Store not found or invalid connection",
            }

        # Create sync log
        sync_log_data = {
            "store_id": ObjectId(store_id),
            "seller_id": store["seller_id"],
            "platform": store["platform"],
            "sync_type": sync_type.value,
            "sync_direction": sync_direction.value,
            "status": SyncStatus.STARTED.value,
            "triggered_by": triggered_by,
            "triggered_by_user_id": ObjectId(user_id) if user_id else None,
            "api_calls_made": 0,
            "started_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        sync_result = await self.sync_logs_collection.insert_one(sync_log_data)
        sync_log_id = sync_result.inserted_id

        # Update store sync status
        await self.stores_collection.update_one(
            {"_id": ObjectId(store_id)},
            {
                "$set": {
                    "last_sync_status": SyncStatus.SYNCING.value,
                    "last_sync_at": datetime.utcnow(),
                },
                "$inc": {"total_syncs": 1},
            }
        )

        try:
            # Perform sync based on type
            if sync_type == SyncType.INVENTORY:
                result = await self._sync_inventory(store, adapter, sync_direction)
            elif sync_type == SyncType.ORDERS:
                result = await self._sync_orders(store, adapter, sync_direction)
            elif sync_type == SyncType.PRODUCTS:
                result = await self._sync_products(store, adapter, sync_direction)
            elif sync_type == SyncType.STREAM_DATA:
                result = await self._sync_stream_data(store, adapter)
            elif sync_type == SyncType.FULL_SYNC:
                result = await self._full_sync(store, adapter)
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported sync type: {sync_type}",
                }

            # Determine final status
            final_status = SyncStatus.SUCCESS if result.get("success") else SyncStatus.FAILED
            if result.get("partial"):
                final_status = SyncStatus.PARTIAL_SUCCESS

            # Update sync log with results
            duration = (datetime.utcnow() - sync_log_data["started_at"]).total_seconds()
            await self.sync_logs_collection.update_one(
                {"_id": sync_log_id},
                {
                    "$set": {
                        "status": final_status.value,
                        "result": result.get("result", {}),
                        "error_message": result.get("error"),
                        "duration_seconds": duration,
                        "api_calls_made": result.get("api_calls", 0),
                        "completed_at": datetime.utcnow(),
                    }
                }
            )

            # Update store statistics
            update_fields = {
                "last_sync_status": final_status.value,
                "last_sync_at": datetime.utcnow(),
            }
            if final_status == SyncStatus.SUCCESS:
                await self.stores_collection.update_one(
                    {"_id": ObjectId(store_id)},
                    {
                        "$set": update_fields,
                        "$inc": {"successful_syncs": 1},
                    }
                )
            else:
                await self.stores_collection.update_one(
                    {"_id": ObjectId(store_id)},
                    {
                        "$set": {
                            **update_fields,
                            "last_sync_error": result.get("error"),
                        },
                        "$inc": {"failed_syncs": 1},
                    }
                )

            return {
                "success": result.get("success", False),
                "sync_log_id": str(sync_log_id),
                "result": result.get("result"),
                "message": result.get("message", "Sync completed"),
            }

        except Exception as e:
            # Handle unexpected errors
            await self.sync_logs_collection.update_one(
                {"_id": sync_log_id},
                {
                    "$set": {
                        "status": SyncStatus.FAILED.value,
                        "error_message": str(e),
                        "completed_at": datetime.utcnow(),
                    }
                }
            )
            await self.stores_collection.update_one(
                {"_id": ObjectId(store_id)},
                {
                    "$set": {
                        "last_sync_status": SyncStatus.FAILED.value,
                        "last_sync_error": str(e),
                    },
                    "$inc": {"failed_syncs": 1},
                }
            )
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}",
                "sync_log_id": str(sync_log_id),
            }

    async def _sync_inventory(
        self,
        store: Dict,
        adapter: Any,
        direction: SyncDirection,
    ) -> Dict[str, Any]:
        """Sync inventory data"""
        if direction == SyncDirection.PULL:
            # Fetch inventory from platform
            inventory_data = await adapter.fetch_inventory(store["store_id"], page_size=100)
            items = inventory_data.get("items", [])

            # Mock: simulate updating local inventory
            updated_count = len(items)

            return {
                "success": True,
                "api_calls": 1,
                "result": {
                    "total_items": len(items),
                    "processed_items": updated_count,
                    "successful_items": updated_count,
                    "failed_items": 0,
                    "updated_count": updated_count,
                },
            }
        else:  # PUSH
            # Mock: push inventory to platform
            return {
                "success": True,
                "api_calls": 1,
                "result": {
                    "total_items": 10,
                    "processed_items": 10,
                    "successful_items": 10,
                    "failed_items": 0,
                    "updated_count": 10,
                },
            }

    async def _sync_orders(
        self,
        store: Dict,
        adapter: Any,
        direction: SyncDirection,
    ) -> Dict[str, Any]:
        """Sync orders data"""
        if direction == SyncDirection.PULL:
            # Fetch orders from platform
            orders_data = await adapter.fetch_orders(store["store_id"], page_size=100)
            orders = orders_data.get("orders", [])

            # Mock: simulate importing orders
            imported_count = len(orders)

            return {
                "success": True,
                "api_calls": 1,
                "result": {
                    "total_items": len(orders),
                    "processed_items": imported_count,
                    "successful_items": imported_count,
                    "failed_items": 0,
                    "created_count": imported_count,
                },
            }
        else:
            return {
                "success": True,
                "api_calls": 0,
                "result": {
                    "total_items": 0,
                    "processed_items": 0,
                    "successful_items": 0,
                    "failed_items": 0,
                },
                "message": "Order push not supported",
            }

    async def _sync_products(
        self,
        store: Dict,
        adapter: Any,
        direction: SyncDirection,
    ) -> Dict[str, Any]:
        """Sync product catalog"""
        if direction == SyncDirection.PULL:
            # Fetch products from platform
            products_data = await adapter.fetch_products(store["store_id"], page_size=100)
            products = products_data.get("products", [])

            # Mock: simulate importing products
            imported_count = len(products)

            return {
                "success": True,
                "api_calls": 1,
                "result": {
                    "total_items": len(products),
                    "processed_items": imported_count,
                    "successful_items": imported_count,
                    "failed_items": 0,
                    "created_count": imported_count,
                },
            }
        else:  # PUSH
            # Mock: push products to platform
            return {
                "success": True,
                "api_calls": 1,
                "result": {
                    "total_items": 15,
                    "processed_items": 15,
                    "successful_items": 15,
                    "failed_items": 0,
                    "created_count": 15,
                },
            }

    async def _sync_stream_data(
        self,
        store: Dict,
        adapter: Any,
    ) -> Dict[str, Any]:
        """Sync live stream analytics data"""
        # Fetch stream analytics
        analytics_data = await adapter.get_stream_analytics(store["store_id"])
        streams = analytics_data.get("streams", [])

        # Mock: simulate importing stream data
        imported_count = len(streams)

        return {
            "success": True,
            "api_calls": 1,
            "result": {
                "total_items": len(streams),
                "processed_items": imported_count,
                "successful_items": imported_count,
                "failed_items": 0,
                "created_count": imported_count,
            },
        }

    async def _full_sync(
        self,
        store: Dict,
        adapter: Any,
    ) -> Dict[str, Any]:
        """Perform full synchronization of all data types"""
        results = {
            "inventory": await self._sync_inventory(store, adapter, SyncDirection.PULL),
            "orders": await self._sync_orders(store, adapter, SyncDirection.PULL),
            "products": await self._sync_products(store, adapter, SyncDirection.PULL),
            "stream_data": await self._sync_stream_data(store, adapter),
        }

        # Aggregate results
        total_api_calls = sum(r.get("api_calls", 0) for r in results.values())
        all_successful = all(r.get("success", False) for r in results.values())

        combined_result = {
            "inventory": results["inventory"].get("result"),
            "orders": results["orders"].get("result"),
            "products": results["products"].get("result"),
            "stream_data": results["stream_data"].get("result"),
        }

        return {
            "success": all_successful,
            "api_calls": total_api_calls,
            "result": combined_result,
            "message": "Full sync completed",
        }

    async def get_sync_history(
        self,
        store_id: Optional[str] = None,
        platform: Optional[Platform] = None,
        sync_type: Optional[SyncType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get sync operation history"""
        query = {}
        if store_id:
            query["store_id"] = ObjectId(store_id)
        if platform:
            query["platform"] = platform.value
        if sync_type:
            query["sync_type"] = sync_type.value

        total = await self.sync_logs_collection.count_documents(query)

        cursor = (
            self.sync_logs_collection.find(query)
            .sort("started_at", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        logs = await cursor.to_list(length=page_size)

        # Convert ObjectIds to strings
        for log in logs:
            log["_id"] = str(log["_id"])
            log["store_id"] = str(log["store_id"])
            log["seller_id"] = str(log["seller_id"])
            if log.get("triggered_by_user_id"):
                log["triggered_by_user_id"] = str(log["triggered_by_user_id"])

        return {
            "syncs": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_sync_status(self, store_id: str) -> Dict[str, Any]:
        """Get current sync status for a store"""
        store = await self.stores_collection.find_one({"_id": ObjectId(store_id)})
        if not store:
            return {"error": "Store not found"}

        # Check for currently running sync
        current_sync = await self.sync_logs_collection.find_one({
            "store_id": ObjectId(store_id),
            "status": {"$in": [SyncStatus.STARTED.value, SyncStatus.IN_PROGRESS.value]},
        })

        # Get last successful sync
        last_successful = await self.sync_logs_collection.find_one({
            "store_id": ObjectId(store_id),
            "status": SyncStatus.SUCCESS.value,
        }, sort=[("completed_at", -1)])

        # Get today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = await self.sync_logs_collection.aggregate([
            {
                "$match": {
                    "store_id": ObjectId(store_id),
                    "started_at": {"$gte": today_start},
                }
            },
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                }
            }
        ]).to_list(length=10)

        stats_dict = {stat["_id"]: stat["count"] for stat in today_stats}
        total_today = sum(stats_dict.values())
        successful_today = stats_dict.get(SyncStatus.SUCCESS.value, 0)
        failed_today = stats_dict.get(SyncStatus.FAILED.value, 0)

        return {
            "store_id": store_id,
            "platform": store["platform"],
            "is_syncing": current_sync is not None,
            "current_sync": self._format_sync_log(current_sync) if current_sync else None,
            "last_successful_sync": self._format_sync_log(last_successful) if last_successful else None,
            "total_syncs_today": total_today,
            "successful_syncs_today": successful_today,
            "failed_syncs_today": failed_today,
            "success_rate_today": (successful_today / total_today * 100) if total_today > 0 else 0,
        }

    def _format_sync_log(self, log: Dict) -> Dict:
        """Format sync log for response"""
        if not log:
            return None
        formatted = {**log}
        formatted["_id"] = str(log["_id"])
        formatted["store_id"] = str(log["store_id"])
        formatted["seller_id"] = str(log["seller_id"])
        if log.get("triggered_by_user_id"):
            formatted["triggered_by_user_id"] = str(log["triggered_by_user_id"])
        return formatted
