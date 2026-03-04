"""Database Seeding Script for Logistics

Populates the database with sample logistics data including carriers,
delivery zones, shipments, and tracking events.
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import random

from app.models.logistics import (
    Carrier,
    DeliveryZone,
    Shipment,
    TrackingEvent,
    ShipmentStatus,
    Address,
    PackageDetails
)


async def seed_logistics_database(db: AsyncIOMotorDatabase):
    """Seed logistics collections with sample data"""

    # Clear existing data
    await db.carriers.delete_many({})
    await db.delivery_zones.delete_many({})
    await db.shipments.delete_many({})
    await db.tracking_events.delete_many({})

    print("Seeding carriers...")

    # Create carriers
    carriers_data = [
        {
            "name": {"en": "Taobao Logistics", "ko": "타오바오 물류"},
            "code": "taobao",
            "country": "China",
            "api_endpoint": "https://api.taobao.com/logistics",
            "supports_tracking": True,
            "supports_webhooks": True,
            "is_active": True
        },
        {
            "name": {"en": "SF Express", "ko": "SF익스프레스"},
            "code": "sf-express",
            "country": "China",
            "api_endpoint": "https://api.sf-express.com",
            "supports_tracking": True,
            "supports_webhooks": False,
            "is_active": True
        },
        {
            "name": {"en": "CJ Logistics", "ko": "CJ대한통운"},
            "code": "cj-logistics",
            "country": "South Korea",
            "api_endpoint": "https://api.cjlogistics.com",
            "supports_tracking": True,
            "supports_webhooks": True,
            "is_active": True
        },
        {
            "name": {"en": "Korea Post", "ko": "우체국택배"},
            "code": "korea-post",
            "country": "South Korea",
            "api_endpoint": None,
            "supports_tracking": True,
            "supports_webhooks": False,
            "is_active": True
        },
        {
            "name": {"en": "China Post", "ko": "중국우정"},
            "code": "china-post",
            "country": "China",
            "api_endpoint": None,
            "supports_tracking": True,
            "supports_webhooks": False,
            "is_active": False  # Inactive carrier
        }
    ]

    carriers = []
    for carrier_data in carriers_data:
        carrier = Carrier(**carrier_data)
        result = await db.carriers.insert_one(carrier.model_dump(by_alias=True, exclude={"id"}))
        carrier.id = result.inserted_id
        carriers.append(carrier)

    print(f"Created {len(carriers)} carriers")

    # Create delivery zones
    print("Seeding delivery zones...")

    delivery_zones_data = [
        # Taobao Logistics zones
        {
            "name": {"en": "China to Korea - Standard", "ko": "중국발 한국행 - 표준"},
            "carrier_id": carriers[0].id,  # Taobao
            "origin_country": "China",
            "destination_country": "South Korea",
            "destination_regions": [],
            "base_cost": 15.0,
            "per_kg_cost": 8.0,
            "weight_min": 0.0,
            "weight_max": 30.0,
            "estimated_days_min": 5,
            "estimated_days_max": 7,
            "is_active": True
        },
        {
            "name": {"en": "China to Korea - Express", "ko": "중국발 한국행 - 특급"},
            "carrier_id": carriers[0].id,  # Taobao
            "origin_country": "China",
            "destination_country": "South Korea",
            "destination_regions": [],
            "base_cost": 25.0,
            "per_kg_cost": 12.0,
            "weight_min": 0.0,
            "weight_max": 20.0,
            "estimated_days_min": 2,
            "estimated_days_max": 3,
            "is_active": True
        },
        # SF Express zones
        {
            "name": {"en": "China to Korea - Premium", "ko": "중국발 한국행 - 프리미엄"},
            "carrier_id": carriers[1].id,  # SF Express
            "origin_country": "China",
            "destination_country": "South Korea",
            "destination_regions": [],
            "base_cost": 30.0,
            "per_kg_cost": 15.0,
            "weight_min": 0.0,
            "weight_max": 50.0,
            "estimated_days_min": 1,
            "estimated_days_max": 2,
            "is_active": True
        },
        # CJ Logistics zones
        {
            "name": {"en": "Korea to China - Standard", "ko": "한국발 중국행 - 표준"},
            "carrier_id": carriers[2].id,  # CJ Logistics
            "origin_country": "South Korea",
            "destination_country": "China",
            "destination_regions": ["Beijing", "Shanghai", "Guangzhou"],
            "base_cost": 20.0,
            "per_kg_cost": 10.0,
            "weight_min": 0.0,
            "weight_max": 40.0,
            "estimated_days_min": 4,
            "estimated_days_max": 6,
            "is_active": True
        },
        {
            "name": {"en": "Korea Domestic", "ko": "국내배송"},
            "carrier_id": carriers[2].id,  # CJ Logistics
            "origin_country": "South Korea",
            "destination_country": "South Korea",
            "destination_regions": [],
            "base_cost": 3.0,
            "per_kg_cost": 2.0,
            "weight_min": 0.0,
            "weight_max": 100.0,
            "estimated_days_min": 1,
            "estimated_days_max": 3,
            "is_active": True
        },
        # Korea Post zones
        {
            "name": {"en": "Korea to China - Economy", "ko": "한국발 중국행 - 이코노미"},
            "carrier_id": carriers[3].id,  # Korea Post
            "origin_country": "South Korea",
            "destination_country": "China",
            "destination_regions": [],
            "base_cost": 12.0,
            "per_kg_cost": 6.0,
            "weight_min": 0.0,
            "weight_max": 20.0,
            "estimated_days_min": 7,
            "estimated_days_max": 10,
            "is_active": True
        }
    ]

    delivery_zones = []
    for zone_data in delivery_zones_data:
        zone = DeliveryZone(**zone_data)
        result = await db.delivery_zones.insert_one(zone.model_dump(by_alias=True, exclude={"id"}))
        zone.id = result.inserted_id
        delivery_zones.append(zone)

    print(f"Created {len(delivery_zones)} delivery zones")

    # Get sample orders for creating shipments
    print("Fetching sample orders...")
    orders_cursor = db.orders.find().limit(100)
    orders = await orders_cursor.to_list(length=100)

    if not orders:
        print("No orders found! Please seed orders first.")
        return

    # Get sample warehouses
    warehouses_cursor = db.warehouses.find().limit(3)
    warehouses = await warehouses_cursor.to_list(length=3)

    print(f"Found {len(orders)} orders for seeding shipments...")

    # We'll create 100 shipments, reusing orders if needed
    num_shipments_to_create = 100

    # Create shipments
    shipments = []
    shipment_statuses = [
        ShipmentStatus.PENDING,
        ShipmentStatus.PICKED_UP,
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.OUT_FOR_DELIVERY,
        ShipmentStatus.DELIVERED,
        ShipmentStatus.FAILED
    ]

    # Sample Korean and Chinese addresses
    korean_addresses = [
        {"city": "Seoul", "postal_code": "06234", "country": "South Korea"},
        {"city": "Busan", "postal_code": "48058", "country": "South Korea"},
        {"city": "Incheon", "postal_code": "22711", "country": "South Korea"},
        {"city": "Daegu", "postal_code": "42642", "country": "South Korea"}
    ]

    chinese_addresses = [
        {"city": "Beijing", "postal_code": "100000", "country": "China"},
        {"city": "Shanghai", "postal_code": "200000", "country": "China"},
        {"city": "Guangzhou", "postal_code": "510000", "country": "China"},
        {"city": "Shenzhen", "postal_code": "518000", "country": "China"}
    ]

    for i in range(num_shipments_to_create):
        # Cycle through orders if we don't have enough
        order = orders[i % len(orders)]

        # Select carrier and delivery zone
        carrier = random.choice(carriers[:4])  # Exclude inactive carrier

        # Find matching delivery zone
        matching_zones = [z for z in delivery_zones if z.carrier_id == carrier.id]
        if not matching_zones:
            continue

        delivery_zone = random.choice(matching_zones)

        # Determine origin and destination based on delivery zone
        if delivery_zone.origin_country == "China":
            origin_addr = random.choice(chinese_addresses)
            dest_addr = random.choice(korean_addresses)
        else:
            origin_addr = random.choice(korean_addresses)
            dest_addr = random.choice(chinese_addresses)

        # Create addresses
        origin = Address(
            name="Warehouse " + chr(65 + (i % 3)),
            phone="+86-21-1234-5678" if origin_addr["country"] == "China" else "+82-2-1234-5678",
            address_line1=f"{random.randint(1, 999)} Commerce Street",
            city=origin_addr["city"],
            postal_code=origin_addr["postal_code"],
            country=origin_addr["country"]
        )

        destination = Address(
            name=f"Customer {chr(65 + (i % 26))}",  # Cycle through A-Z
            phone="+82-10-1234-5678" if dest_addr["country"] == "South Korea" else "+86-138-1234-5678",
            address_line1=f"{random.randint(1, 999)} Main Street, Apt {random.randint(100, 999)}",
            city=dest_addr["city"],
            postal_code=dest_addr["postal_code"],
            country=dest_addr["country"]
        )

        # Create package details
        weight = round(random.uniform(0.5, 10.0), 2)
        package_details = PackageDetails(
            weight=weight,
            length=round(random.uniform(10, 50), 2),
            width=round(random.uniform(10, 40), 2),
            height=round(random.uniform(5, 30), 2),
            declared_value=round(random.uniform(20, 500), 2)
        )

        # Create shipment
        status = random.choice(shipment_statuses)
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        shipment = Shipment(
            order_id=order["_id"],
            shipment_number=f"SHP-{created_at.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            carrier_id=carrier.id,
            tracking_number=f"TRK{random.randint(100000000, 999999999)}",
            status=status,
            origin=origin,
            destination=destination,
            package_details=package_details,
            warehouse_id=warehouses[i % len(warehouses)]["_id"] if warehouses else None,
            delivery_zone_id=delivery_zone.id,
            shipping_cost=round(delivery_zone.calculate_cost(weight), 2),
            created_at=created_at,
            updated_at=created_at
        )

        # Set estimated and actual delivery dates
        avg_days = (delivery_zone.estimated_days_min + delivery_zone.estimated_days_max) / 2
        shipment.estimated_delivery_date = created_at + timedelta(days=avg_days)

        if status in [ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY]:
            shipment.shipped_at = created_at + timedelta(hours=random.randint(2, 24))
        elif status == ShipmentStatus.DELIVERED:
            shipment.shipped_at = created_at + timedelta(hours=random.randint(2, 24))
            delivery_days = max(1, int(avg_days))  # Ensure at least 1 day
            shipment.delivered_at = created_at + timedelta(days=random.randint(1, delivery_days))
            shipment.actual_delivery_date = shipment.delivered_at

        result = await db.shipments.insert_one(shipment.model_dump(by_alias=True, exclude={"id"}))
        shipment.id = result.inserted_id
        shipments.append(shipment)

    print(f"Created {len(shipments)} shipments")

    # Create tracking events
    print("Seeding tracking events...")

    tracking_descriptions = {
        ShipmentStatus.PENDING: {
            "en": "Shipment created and awaiting pickup",
            "ko": "배송이 생성되었으며 픽업을 기다리고 있습니다"
        },
        ShipmentStatus.PICKED_UP: {
            "en": "Package picked up by courier",
            "ko": "택배기사가 물품을 픽업했습니다"
        },
        ShipmentStatus.IN_TRANSIT: {
            "en": "Package in transit to destination",
            "ko": "목적지로 이동 중입니다"
        },
        ShipmentStatus.OUT_FOR_DELIVERY: {
            "en": "Out for delivery",
            "ko": "배송중입니다"
        },
        ShipmentStatus.DELIVERED: {
            "en": "Package delivered successfully",
            "ko": "성공적으로 배송되었습니다"
        },
        ShipmentStatus.FAILED: {
            "en": "Delivery failed - recipient unavailable",
            "ko": "배송 실패 - 수취인 부재"
        }
    }

    tracking_events = []
    for shipment in shipments:
        # Create tracking events based on shipment status
        events_to_create = []

        if shipment.status == ShipmentStatus.PENDING:
            events_to_create = [ShipmentStatus.PENDING]
        elif shipment.status == ShipmentStatus.PICKED_UP:
            events_to_create = [ShipmentStatus.PENDING, ShipmentStatus.PICKED_UP]
        elif shipment.status == ShipmentStatus.IN_TRANSIT:
            events_to_create = [ShipmentStatus.PENDING, ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT]
        elif shipment.status == ShipmentStatus.OUT_FOR_DELIVERY:
            events_to_create = [ShipmentStatus.PENDING, ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY]
        elif shipment.status == ShipmentStatus.DELIVERED:
            events_to_create = [ShipmentStatus.PENDING, ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.DELIVERED]
        elif shipment.status == ShipmentStatus.FAILED:
            events_to_create = [ShipmentStatus.PENDING, ShipmentStatus.PICKED_UP, ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.FAILED]

        event_time = shipment.created_at
        for event_status in events_to_create:
            event = TrackingEvent(
                shipment_id=shipment.id,
                status=event_status,
                location=shipment.origin.city if event_status == ShipmentStatus.PENDING else shipment.destination.city,
                description=tracking_descriptions[event_status],
                event_time=event_time
            )

            result = await db.tracking_events.insert_one(event.model_dump(by_alias=True, exclude={"id"}))
            event.id = result.inserted_id
            tracking_events.append(event)

            # Increment event time
            event_time += timedelta(hours=random.randint(6, 48))

    print(f"Created {len(tracking_events)} tracking events")

    print("\nLogistics database seeding completed successfully!")
    print(f"Summary:")
    print(f"  - Carriers: {len(carriers)}")
    print(f"  - Delivery Zones: {len(delivery_zones)}")
    print(f"  - Shipments: {len(shipments)}")
    print(f"  - Tracking Events: {len(tracking_events)}")
