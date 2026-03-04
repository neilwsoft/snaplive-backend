"""Inventory Service

Business logic for inventory management operations.
"""

from datetime import datetime
from typing import Optional, List, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.inventory import (
    Inventory,
    InventoryLog,
    InventoryAction,
    Warehouse,
    StockAlert,
    AlertType,
    InventoryStatus,
    ProductCategory
)
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    RestockRequest,
    ReserveStockRequest,
    WarehouseCreate
)


class InventoryService:
    """Service for inventory management operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.inventory_collection = db.inventory
        self.logs_collection = db.inventory_logs
        self.warehouses_collection = db.warehouses
        self.alerts_collection = db.stock_alerts

    # Warehouse Operations

    async def create_warehouse(self, warehouse_data: WarehouseCreate) -> Warehouse:
        """Create a new warehouse"""
        warehouse = Warehouse(**warehouse_data.model_dump())
        result = await self.warehouses_collection.insert_one(
            warehouse.model_dump(by_alias=True, exclude={"id"})
        )
        warehouse.id = result.inserted_id
        return warehouse

    async def get_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        """Get a warehouse by ID"""
        doc = await self.warehouses_collection.find_one({"_id": ObjectId(warehouse_id)})
        if doc:
            return Warehouse(**doc)
        return None

    async def list_warehouses(self) -> List[Warehouse]:
        """Get all warehouses"""
        cursor = self.warehouses_collection.find({})
        warehouses = []
        async for doc in cursor:
            warehouses.append(Warehouse(**doc))
        return warehouses

    # Inventory CRUD Operations

    async def create_inventory(self, inventory_data: InventoryCreate) -> Inventory:
        """Create a new inventory item"""
        # Validate warehouse exists
        warehouse = await self.get_warehouse(inventory_data.warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse {inventory_data.warehouse_id} not found")

        # Create inventory item
        inventory = Inventory(**inventory_data.model_dump())
        inventory.warehouse_id = ObjectId(inventory_data.warehouse_id)

        result = await self.inventory_collection.insert_one(
            inventory.model_dump(by_alias=True, exclude={"id"})
        )
        inventory.id = result.inserted_id

        # Create initial log
        await self._create_log(
            inventory_id=inventory.id,
            product_name=inventory.product_name,
            warehouse_id=inventory.warehouse_id,
            action=InventoryAction.ADJUSTMENT,
            quantity_change=inventory.quantity,
            previous_quantity=0,
            new_quantity=inventory.quantity,
            notes="Initial inventory creation"
        )

        # Check and create alerts if needed
        await self._check_and_create_alerts(inventory)

        return inventory

    async def get_inventory(self, inventory_id: str) -> Optional[Inventory]:
        """Get an inventory item by ID"""
        doc = await self.inventory_collection.find_one({"_id": ObjectId(inventory_id)})
        if doc:
            return Inventory(**doc)
        return None

    async def list_inventory(
        self,
        warehouse_id: Optional[str] = None,
        stock_status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Inventory], int]:
        """List inventory items with filters"""
        query = {}

        if warehouse_id:
            query["warehouse_id"] = ObjectId(warehouse_id)

        if category:
            query["category"] = category

        if search:
            query["$or"] = [
                {"sku": {"$regex": search, "$options": "i"}},
                {"product_name.en": {"$regex": search, "$options": "i"}},
                {"product_name.ko": {"$regex": search, "$options": "i"}},
            ]

        # Get total count
        total = await self.inventory_collection.count_documents(query)

        # Get items
        cursor = self.inventory_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        items = []
        async for doc in cursor:
            inventory = Inventory(**doc)

            # Filter by stock status if specified
            if stock_status == "low" and not inventory.is_low_stock:
                continue
            elif stock_status == "critical" and not inventory.is_critical_stock:
                continue
            elif stock_status == "normal" and (inventory.is_low_stock or inventory.is_critical_stock):
                continue

            items.append(inventory)

        return items, total

    async def update_inventory(
        self,
        inventory_id: str,
        update_data: InventoryUpdate
    ) -> Optional[Inventory]:
        """Update an inventory item"""
        inventory = await self.get_inventory(inventory_id)
        if not inventory:
            return None

        # Prepare update dict
        update_dict = update_data.model_dump(exclude_unset=True)
        if "warehouse_id" in update_dict:
            update_dict["warehouse_id"] = ObjectId(update_dict["warehouse_id"])
        update_dict["updated_at"] = datetime.utcnow()

        # Perform update
        await self.inventory_collection.update_one(
            {"_id": ObjectId(inventory_id)},
            {"$set": update_dict}
        )

        # Get updated inventory
        updated_inventory = await self.get_inventory(inventory_id)

        # Check alerts after update
        if updated_inventory:
            await self._check_and_create_alerts(updated_inventory)

        return updated_inventory

    async def delete_inventory(self, inventory_id: str) -> bool:
        """Delete an inventory item"""
        result = await self.inventory_collection.delete_one({"_id": ObjectId(inventory_id)})

        # Also delete related alerts
        await self.alerts_collection.delete_many({"inventory_id": ObjectId(inventory_id)})

        return result.deleted_count > 0

    # Stock Operations

    async def restock_inventory(
        self,
        restock_data: RestockRequest,
        user_id: Optional[str] = None
    ) -> Optional[Inventory]:
        """Add stock to inventory"""
        inventory = await self.get_inventory(restock_data.inventory_id)
        if not inventory:
            return None

        previous_quantity = inventory.quantity
        new_quantity = previous_quantity + restock_data.quantity

        # Update inventory
        await self.inventory_collection.update_one(
            {"_id": ObjectId(restock_data.inventory_id)},
            {
                "$set": {
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Create log
        await self._create_log(
            inventory_id=inventory.id,
            product_name=inventory.product_name,
            warehouse_id=inventory.warehouse_id,
            action=InventoryAction.RESTOCK,
            quantity_change=restock_data.quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            notes=restock_data.notes,
            created_by=user_id
        )

        # Get updated inventory and check alerts
        updated_inventory = await self.get_inventory(restock_data.inventory_id)
        if updated_inventory:
            await self._check_and_create_alerts(updated_inventory)

        return updated_inventory

    async def reserve_stock(
        self,
        reserve_data: ReserveStockRequest,
        user_id: Optional[str] = None
    ) -> Optional[Inventory]:
        """Reserve stock for an order"""
        inventory = await self.get_inventory(reserve_data.inventory_id)
        if not inventory:
            return None

        # Check if enough stock available
        if inventory.available < reserve_data.quantity:
            raise ValueError(f"Insufficient stock. Available: {inventory.available}, Requested: {reserve_data.quantity}")

        previous_reserved = inventory.reserved
        new_reserved = previous_reserved + reserve_data.quantity

        # Update reserved quantity
        await self.inventory_collection.update_one(
            {"_id": ObjectId(reserve_data.inventory_id)},
            {
                "$set": {
                    "reserved": new_reserved,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Create log
        await self._create_log(
            inventory_id=inventory.id,
            product_name=inventory.product_name,
            warehouse_id=inventory.warehouse_id,
            action=InventoryAction.RESERVATION,
            quantity_change=-reserve_data.quantity,
            previous_quantity=inventory.quantity,
            new_quantity=inventory.quantity,
            reference_id=reserve_data.reference_id,
            notes=f"Reserved {reserve_data.quantity} units",
            created_by=user_id
        )

        # Get updated inventory and check alerts
        updated_inventory = await self.get_inventory(reserve_data.inventory_id)
        if updated_inventory:
            await self._check_and_create_alerts(updated_inventory)

        return updated_inventory

    async def release_stock(
        self,
        inventory_id: str,
        quantity: int,
        reference_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Inventory]:
        """Release reserved stock (e.g., when order is cancelled)"""
        inventory = await self.get_inventory(inventory_id)
        if not inventory:
            return None

        # Check if enough reserved stock
        if inventory.reserved < quantity:
            raise ValueError(f"Cannot release {quantity} units. Only {inventory.reserved} reserved.")

        new_reserved = inventory.reserved - quantity

        # Update reserved quantity
        await self.inventory_collection.update_one(
            {"_id": ObjectId(inventory_id)},
            {
                "$set": {
                    "reserved": new_reserved,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Create log
        await self._create_log(
            inventory_id=inventory.id,
            product_name=inventory.product_name,
            warehouse_id=inventory.warehouse_id,
            action=InventoryAction.RELEASE,
            quantity_change=quantity,
            previous_quantity=inventory.quantity,
            new_quantity=inventory.quantity,
            reference_id=reference_id,
            notes=f"Released {quantity} reserved units",
            created_by=user_id
        )

        # Get updated inventory
        updated_inventory = await self.get_inventory(inventory_id)
        return updated_inventory

    # Inventory Logs

    async def get_inventory_logs(
        self,
        inventory_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[InventoryLog], int]:
        """Get inventory change logs"""
        query = {}
        if inventory_id:
            query["inventory_id"] = ObjectId(inventory_id)

        total = await self.logs_collection.count_documents(query)
        cursor = self.logs_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)

        logs = []
        async for doc in cursor:
            logs.append(InventoryLog(**doc))

        return logs, total

    async def _create_log(
        self,
        inventory_id: ObjectId,
        product_name: Dict[str, str],
        warehouse_id: ObjectId,
        action: InventoryAction,
        quantity_change: int,
        previous_quantity: int,
        new_quantity: int,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ):
        """Create an inventory log entry"""
        log = InventoryLog(
            inventory_id=inventory_id,
            product_name=product_name,
            warehouse_id=warehouse_id,
            action=action,
            quantity_change=quantity_change,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by
        )
        await self.logs_collection.insert_one(log.model_dump(by_alias=True, exclude={"id"}))

    # Stock Alerts

    async def get_stock_alerts(
        self,
        acknowledged: Optional[bool] = None
    ) -> List[StockAlert]:
        """Get stock alerts"""
        query = {}
        if acknowledged is not None:
            query["is_acknowledged"] = acknowledged

        cursor = self.alerts_collection.find(query).sort("created_at", -1)
        alerts = []
        async for doc in cursor:
            alerts.append(StockAlert(**doc))

        return alerts

    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: Optional[str] = None
    ) -> Optional[StockAlert]:
        """Acknowledge a stock alert"""
        await self.alerts_collection.update_one(
            {"_id": ObjectId(alert_id)},
            {
                "$set": {
                    "is_acknowledged": True,
                    "acknowledged_at": datetime.utcnow(),
                    "acknowledged_by": user_id
                }
            }
        )

        doc = await self.alerts_collection.find_one({"_id": ObjectId(alert_id)})
        if doc:
            return StockAlert(**doc)
        return None

    async def _check_and_create_alerts(self, inventory: Inventory):
        """Check inventory levels and create alerts if needed"""
        # Remove existing alerts for this inventory
        await self.alerts_collection.delete_many({"inventory_id": inventory.id})

        # Get warehouse info
        warehouse = await self.get_warehouse(str(inventory.warehouse_id))
        if not warehouse:
            return

        # Check for critical stock
        if inventory.is_critical_stock:
            alert = StockAlert(
                inventory_id=inventory.id,
                product_name=inventory.product_name,
                warehouse_id=inventory.warehouse_id,
                warehouse_name=warehouse.name,
                sku=inventory.sku,
                alert_type=AlertType.CRITICAL_STOCK,
                current_level=inventory.available,
                threshold=inventory.critical_level
            )
            await self.alerts_collection.insert_one(
                alert.model_dump(by_alias=True, exclude={"id"})
            )
        # Check for low stock (only if not critical)
        elif inventory.is_low_stock:
            alert = StockAlert(
                inventory_id=inventory.id,
                product_name=inventory.product_name,
                warehouse_id=inventory.warehouse_id,
                warehouse_name=warehouse.name,
                sku=inventory.sku,
                alert_type=AlertType.LOW_STOCK,
                current_level=inventory.available,
                threshold=inventory.reorder_point
            )
            await self.alerts_collection.insert_one(
                alert.model_dump(by_alias=True, exclude={"id"})
            )

    # Categories

    async def get_categories(self) -> List[Dict]:
        """Get all product categories with counts"""
        pipeline = [
            {"$match": {"category": {"$ne": None}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]

        result = await self.inventory_collection.aggregate(pipeline).to_list(100)

        # Build response with all categories (even those with 0 count)
        category_counts = {item["_id"]: item["count"] for item in result}

        categories = []
        for cat in ProductCategory:
            categories.append({
                "value": cat.value,
                "label": cat.value.replace("_", " ").title(),
                "count": category_counts.get(cat.value, 0)
            })

        return categories

    # Statistics

    async def get_inventory_stats(self) -> Dict:
        """Get overall inventory statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_items": {"$sum": 1},
                    "total_quantity": {"$sum": "$quantity"},
                    "total_reserved": {"$sum": "$reserved"},
                    "total_value": {"$sum": {"$multiply": ["$quantity", "$unit_cost"]}}
                }
            }
        ]

        result = await self.inventory_collection.aggregate(pipeline).to_list(1)
        stats = result[0] if result else {
            "total_items": 0,
            "total_quantity": 0,
            "total_reserved": 0,
            "total_value": 0.0
        }

        # Get warehouse count
        warehouses_count = await self.warehouses_collection.count_documents({})

        # Get alert counts
        alerts = await self.get_stock_alerts(acknowledged=False)
        low_stock_count = sum(1 for a in alerts if a.alert_type == AlertType.LOW_STOCK)
        critical_stock_count = sum(1 for a in alerts if a.alert_type == AlertType.CRITICAL_STOCK)

        return {
            "total_items": stats["total_items"],
            "total_warehouses": warehouses_count,
            "low_stock_count": low_stock_count,
            "critical_stock_count": critical_stock_count,
            "total_quantity": stats["total_quantity"],
            "total_reserved": stats["total_reserved"],
            "total_available": stats["total_quantity"] - stats["total_reserved"],
            "total_value": stats["total_value"]
        }
