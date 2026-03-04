"""Inventory Database Seeding Script

Populates MongoDB with realistic inventory dummy data for testing.
"""

from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.inventory import (
    Warehouse,
    Inventory,
    InventoryLog,
    InventoryAction,
    InventoryStatus,
    StockAlert,
    AlertType,
    ProductCategory
)


async def seed_warehouses(db: AsyncIOMotorDatabase) -> dict[str, ObjectId]:
    """Seed warehouse data"""
    print("Seeding warehouses...")

    warehouses = [
        Warehouse(
            name={
                "en": "Seoul Main Warehouse",
                "ko": "서울 메인 창고"
            },
            location="123 Gangnam-daero, Gangnam-gu",
            city="Seoul",
            country="South Korea",
            is_default=True
        ),
        Warehouse(
            name={
                "en": "Busan Distribution Center",
                "ko": "부산 물류센터"
            },
            location="456 Haeundae Beach Road, Haeundae-gu",
            city="Busan",
            country="South Korea",
            is_default=False
        ),
        Warehouse(
            name={
                "en": "Incheon Storage Facility",
                "ko": "인천 보관 시설"
            },
            location="789 Airport Road, Jung-gu",
            city="Incheon",
            country="South Korea",
            is_default=False
        )
    ]

    warehouse_ids = {}
    for warehouse in warehouses:
        result = await db.warehouses.insert_one(
            warehouse.model_dump(by_alias=True, exclude={"id"})
        )
        warehouse_ids[warehouse.name["en"]] = result.inserted_id
        print(f"  ✓ Created: {warehouse.name['en']}")

    return warehouse_ids


async def seed_inventory(db: AsyncIOMotorDatabase, warehouse_ids: dict) -> list[ObjectId]:
    """Seed inventory data"""
    print("\nSeeding inventory items...")

    seoul_id = warehouse_ids["Seoul Main Warehouse"]
    busan_id = warehouse_ids["Busan Distribution Center"]
    incheon_id = warehouse_ids["Incheon Storage Facility"]

    inventory_items = [
        # Normal stock items
        Inventory(
            product_id="prod_001",
            product_name={"en": "Premium Korean Kimchi 1kg", "ko": "프리미엄 한국 김치 1kg"},
            warehouse_id=seoul_id,
            quantity=150,
            reserved=20,
            reorder_point=50,
            critical_level=20,
            sku="KIMCHI-1KG-001",
            unit_cost=8.50,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1583224994076-23c82ef1a06c?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_002",
            product_name={"en": "Korean Gochujang 500g", "ko": "한국 고추장 500g"},
            warehouse_id=seoul_id,
            quantity=200,
            reserved=15,
            reorder_point=60,
            critical_level=25,
            sku="GOCHUJANG-500G-001",
            unit_cost=6.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1635865165118-917ed9e20e3d?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_003",
            product_name={"en": "Korean Skincare Set", "ko": "한국 화장품 세트"},
            warehouse_id=busan_id,
            quantity=80,
            reserved=5,
            reorder_point=30,
            critical_level=10,
            sku="COSMETIC-SET-001",
            unit_cost=45.00,
            category=ProductCategory.BEAUTY,
            image_url="https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_004",
            product_name={"en": "Instant Ramen 20-Pack", "ko": "즉석 라면 20개입"},
            warehouse_id=seoul_id,
            quantity=120,
            reserved=10,
            reorder_point=40,
            critical_level=15,
            sku="RAMEN-20PK-001",
            unit_cost=18.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_005",
            product_name={"en": "Seaweed Gift Set", "ko": "김 선물세트"},
            warehouse_id=incheon_id,
            quantity=95,
            reserved=8,
            reorder_point=35,
            critical_level=12,
            sku="SEAWEED-GIFT-001",
            unit_cost=12.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_006",
            product_name={"en": "Korean Face Mask 10-Pack", "ko": "한국 페이스 마스크 10팩"},
            warehouse_id=busan_id,
            quantity=160,
            reserved=12,
            reorder_point=50,
            critical_level=20,
            sku="FACEMASK-10PK-001",
            unit_cost=15.00,
            category=ProductCategory.BEAUTY,
            image_url="https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_007",
            product_name={"en": "Ginseng Tea 50-Pack", "ko": "인삼차 50포"},
            warehouse_id=seoul_id,
            quantity=75,
            reserved=5,
            reorder_point=30,
            critical_level=10,
            sku="GINSENG-TEA-50-001",
            unit_cost=32.50,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_008",
            product_name={"en": "Korean BBQ Sauce Set", "ko": "한국 BBQ 소스 세트"},
            warehouse_id=seoul_id,
            quantity=110,
            reserved=10,
            reorder_point=40,
            critical_level=15,
            sku="BBQ-SAUCE-SET-001",
            unit_cost=14.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1472476443507-c7a5948772fc?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_009",
            product_name={"en": "Rice Cooker 6-Cup", "ko": "6인용 밥솥"},
            warehouse_id=busan_id,
            quantity=45,
            reserved=3,
            reorder_point=20,
            critical_level=8,
            sku="COOKER-6CUP-001",
            unit_cost=85.00,
            category=ProductCategory.ELECTRONICS,
            image_url="https://images.unsplash.com/photo-1585664811087-47f65abbad64?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_010",
            product_name={"en": "Korean Snack Variety Pack", "ko": "한국 스낵 모음 팩"},
            warehouse_id=incheon_id,
            quantity=135,
            reserved=15,
            reorder_point=50,
            critical_level=20,
            sku="SNACK-VARIETY-001",
            unit_cost=22.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),

        # Low stock items (available > critical but <= reorder_point)
        Inventory(
            product_id="prod_011",
            product_name={"en": "Korean Soy Sauce 1L", "ko": "한국 간장 1L"},
            warehouse_id=seoul_id,
            quantity=42,
            reserved=10,
            reorder_point=50,
            critical_level=15,
            sku="SOYSAUCE-1L-001",
            unit_cost=7.50,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1614563637806-1d0e645e0940?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_012",
            product_name={"en": "Dried Seaweed Sheets 100g", "ko": "건조 김 100g"},
            warehouse_id=busan_id,
            quantity=28,
            reserved=5,
            reorder_point=40,
            critical_level=12,
            sku="SEAWEED-DRY-100G-001",
            unit_cost=5.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_013",
            product_name={"en": "Korean Green Tea Bags 100ct", "ko": "한국 녹차 티백 100개"},
            warehouse_id=seoul_id,
            quantity=35,
            reserved=8,
            reorder_point=45,
            critical_level=15,
            sku="GREENTEA-100CT-001",
            unit_cost=11.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1556881286-fc6915169721?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_014",
            product_name={"en": "Korean Chili Flakes 200g", "ko": "고춧가루 200g"},
            warehouse_id=incheon_id,
            quantity=47,
            reserved=12,
            reorder_point=60,
            critical_level=20,
            sku="CHILI-FLAKES-200G-001",
            unit_cost=9.50,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_015",
            product_name={"en": "Korean Rice Cake 500g", "ko": "한국 떡 500g"},
            warehouse_id=busan_id,
            quantity=22,
            reserved=4,
            reorder_point=35,
            critical_level=10,
            sku="RICECAKE-500G-001",
            unit_cost=8.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1590301157890-4810ed352733?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),

        # Critical stock items (available <= critical_level)
        Inventory(
            product_id="prod_016",
            product_name={"en": "Korean Honey 500ml", "ko": "한국 꿀 500ml"},
            warehouse_id=seoul_id,
            quantity=18,
            reserved=8,
            reorder_point=40,
            critical_level=15,
            sku="HONEY-500ML-001",
            unit_cost=20.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_017",
            product_name={"en": "Korean Sesame Oil 250ml", "ko": "참기름 250ml"},
            warehouse_id=busan_id,
            quantity=12,
            reserved=5,
            reorder_point=35,
            critical_level=12,
            sku="SESAME-OIL-250ML-001",
            unit_cost=13.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_018",
            product_name={"en": "Korean Barley Tea Bags 50ct", "ko": "보리차 티백 50개"},
            warehouse_id=incheon_id,
            quantity=15,
            reserved=7,
            reorder_point=30,
            critical_level=10,
            sku="BARLEYTEA-50CT-001",
            unit_cost=6.50,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1563822249366-3efb23b8e0c9?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_019",
            product_name={"en": "Korean Red Pepper Paste 1kg", "ko": "고추장 1kg"},
            warehouse_id=seoul_id,
            quantity=20,
            reserved=12,
            reorder_point=45,
            critical_level=15,
            sku="REDPEPPER-PASTE-1KG-001",
            unit_cost=16.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1635865165118-917ed9e20e3d?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        ),
        Inventory(
            product_id="prod_020",
            product_name={"en": "Korean Cooking Wine 750ml", "ko": "요리용 청주 750ml"},
            warehouse_id=busan_id,
            quantity=14,
            reserved=6,
            reorder_point=35,
            critical_level=10,
            sku="COOKING-WINE-750ML-001",
            unit_cost=10.00,
            category=ProductCategory.FOOD,
            image_url="https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=200&h=200&fit=crop",
            status=InventoryStatus.ACTIVE
        )
    ]

    inventory_ids = []
    for item in inventory_items:
        result = await db.inventory.insert_one(
            item.model_dump(by_alias=True, exclude={"id"})
        )
        inventory_ids.append(result.inserted_id)
        status = "CRITICAL" if item.is_critical_stock else "LOW" if item.is_low_stock else "OK"
        print(f"  ✓ Created: {item.product_name['en']} (Available: {item.available}) [{status}]")

    return inventory_ids


async def seed_inventory_logs(db: AsyncIOMotorDatabase):
    """Seed inventory log history"""
    print("\nSeeding inventory logs...")

    # Get some inventory items for creating logs
    items = await db.inventory.find({}).limit(10).to_list(10)

    logs = []
    for i, item in enumerate(items):
        # Create a few historical log entries for each item
        base_date = datetime.utcnow() - timedelta(days=30)

        # Initial stock
        logs.append(InventoryLog(
            inventory_id=item["_id"],
            product_name=item["product_name"],
            warehouse_id=item["warehouse_id"],
            action=InventoryAction.ADJUSTMENT,
            quantity_change=item["quantity"],
            previous_quantity=0,
            new_quantity=item["quantity"],
            notes="Initial stock"
        ))

        # Some restocks
        if i % 3 == 0:
            restock_date = base_date + timedelta(days=15)
            logs.append(InventoryLog(
                inventory_id=item["_id"],
                product_name=item["product_name"],
                warehouse_id=item["warehouse_id"],
                action=InventoryAction.RESTOCK,
                quantity_change=50,
                previous_quantity=item["quantity"] - 50,
                new_quantity=item["quantity"],
                notes="Restocked from supplier",
                created_at=restock_date
            ))

        # Some sales
        if i % 2 == 0:
            sale_date = base_date + timedelta(days=20)
            logs.append(InventoryLog(
                inventory_id=item["_id"],
                product_name=item["product_name"],
                warehouse_id=item["warehouse_id"],
                action=InventoryAction.SALE,
                quantity_change=-10,
                previous_quantity=item["quantity"] + 10,
                new_quantity=item["quantity"],
                reference_id="ord_sample_123",
                notes="Sold via order",
                created_at=sale_date
            ))

    # Insert all logs
    if logs:
        log_dicts = [log.model_dump(by_alias=True, exclude={"id"}) for log in logs]
        await db.inventory_logs.insert_many(log_dicts)
        print(f"  ✓ Created {len(logs)} inventory log entries")


async def seed_stock_alerts(db: AsyncIOMotorDatabase):
    """Seed stock alerts for low and critical items"""
    print("\nSeeding stock alerts...")

    # Find all inventory items
    all_items = await db.inventory.find({}).to_list(None)

    alerts = []
    for item_data in all_items:
        item = Inventory(**item_data)
        available = item.available

        # Get warehouse info
        warehouse = await db.warehouses.find_one({"_id": item.warehouse_id})
        if not warehouse:
            continue

        # Create alert if low or critical
        if available <= item.critical_level:
            alerts.append(StockAlert(
                inventory_id=item.id,
                product_name=item.product_name,
                warehouse_id=item.warehouse_id,
                warehouse_name=warehouse["name"],
                sku=item.sku,
                alert_type=AlertType.CRITICAL_STOCK,
                current_level=available,
                threshold=item.critical_level,
                is_acknowledged=False
            ))
        elif available <= item.reorder_point:
            alerts.append(StockAlert(
                inventory_id=item.id,
                product_name=item.product_name,
                warehouse_id=item.warehouse_id,
                warehouse_name=warehouse["name"],
                sku=item.sku,
                alert_type=AlertType.LOW_STOCK,
                current_level=available,
                threshold=item.reorder_point,
                is_acknowledged=False
            ))

    # Insert alerts
    if alerts:
        alert_dicts = [alert.model_dump(by_alias=True, exclude={"id"}) for alert in alerts]
        await db.stock_alerts.insert_many(alert_dicts)
        print(f"  ✓ Created {len(alerts)} stock alerts")
        print(f"    - Critical: {sum(1 for a in alerts if a.alert_type == AlertType.CRITICAL_STOCK)}")
        print(f"    - Low Stock: {sum(1 for a in alerts if a.alert_type == AlertType.LOW_STOCK)}")


async def clear_existing_data(db: AsyncIOMotorDatabase):
    """Clear existing inventory data"""
    print("Clearing existing inventory data...")

    collections = ["inventory", "warehouses", "inventory_logs", "stock_alerts"]
    for collection in collections:
        result = await db[collection].delete_many({})
        print(f"  ✓ Deleted {result.deleted_count} documents from {collection}")


async def seed_inventory_database(db: AsyncIOMotorDatabase):
    """Main seeding function"""
    print("=" * 50)
    print("INVENTORY DATABASE SEEDING")
    print("=" * 50)

    # Clear existing data
    await clear_existing_data(db)

    # Seed in order
    warehouse_ids = await seed_warehouses(db)
    inventory_ids = await seed_inventory(db, warehouse_ids)
    await seed_inventory_logs(db)
    await seed_stock_alerts(db)

    print("\n" + "=" * 50)
    print("SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"\nSummary:")
    print(f"  - Warehouses: {len(warehouse_ids)}")
    print(f"  - Inventory Items: {len(inventory_ids)}")
    print(f"  - Sample Logs Created")
    print(f"  - Alerts Created for Low/Critical Items")
    print("\n")


# Endpoint to trigger seeding (can be added to inventory.py)
async def seed_endpoint(db: AsyncIOMotorDatabase):
    """Endpoint handler for seeding"""
    await seed_inventory_database(db)
    return {"message": "Inventory database seeded successfully"}
