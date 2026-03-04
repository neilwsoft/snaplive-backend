"""Logistics Service

Business logic for logistics management operations.
"""

from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import secrets
import logging

from app.models.logistics import (
    Shipment,
    Carrier,
    DeliveryZone,
    TrackingEvent,
    ShipmentStatus,
    Address,
    PackageDetails
)
from app.schemas.logistics import (
    ShipmentCreate,
    ShipmentUpdate,
    CarrierCreate,
    CarrierUpdate,
    DeliveryZoneCreate,
    DeliveryZoneUpdate,
    TrackingEventCreate,
    ShippingCostQuote
)

logger = logging.getLogger(__name__)


class LogisticsService:
    """Service for logistics management operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.shipments_collection = db.shipments
        self.carriers_collection = db.carriers
        self.delivery_zones_collection = db.delivery_zones
        self.tracking_events_collection = db.tracking_events
        self.orders_collection = db.orders  # For updating order tracking info

    # Carrier Operations

    async def create_carrier(self, carrier_data: CarrierCreate) -> Carrier:
        """Create a new carrier"""
        carrier = Carrier(**carrier_data.model_dump())

        result = await self.carriers_collection.insert_one(
            carrier.model_dump(by_alias=True, exclude={"id"})
        )

        carrier.id = result.inserted_id
        logger.info(f"Created carrier: {carrier.code}")
        return carrier

    async def get_carrier(self, carrier_id: str) -> Optional[Carrier]:
        """Get a carrier by ID"""
        doc = await self.carriers_collection.find_one({"_id": ObjectId(carrier_id)})
        return Carrier(**doc) if doc else None

    async def list_carriers(self, is_active: Optional[bool] = None) -> List[Carrier]:
        """List all carriers"""
        query = {}
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self.carriers_collection.find(query)
        carriers = []
        async for doc in cursor:
            carriers.append(Carrier(**doc))

        return carriers

    async def update_carrier(self, carrier_id: str, update_data: CarrierUpdate) -> Optional[Carrier]:
        """Update a carrier"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if not update_dict:
            return await self.get_carrier(carrier_id)

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.carriers_collection.find_one_and_update(
            {"_id": ObjectId(carrier_id)},
            {"$set": update_dict},
            return_document=True
        )

        return Carrier(**result) if result else None

    # Delivery Zone Operations

    async def create_delivery_zone(self, zone_data: DeliveryZoneCreate) -> DeliveryZone:
        """Create a new delivery zone"""
        zone = DeliveryZone(
            carrier_id=ObjectId(zone_data.carrier_id),
            **zone_data.model_dump(exclude={"carrier_id"})
        )

        result = await self.delivery_zones_collection.insert_one(
            zone.model_dump(by_alias=True, exclude={"id"})
        )

        zone.id = result.inserted_id
        logger.info(f"Created delivery zone for carrier {zone_data.carrier_id}")
        return zone

    async def get_delivery_zone(self, zone_id: str) -> Optional[DeliveryZone]:
        """Get a delivery zone by ID"""
        doc = await self.delivery_zones_collection.find_one({"_id": ObjectId(zone_id)})
        return DeliveryZone(**doc) if doc else None

    async def list_delivery_zones(
        self,
        carrier_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[DeliveryZone]:
        """List delivery zones"""
        query = {}
        if carrier_id:
            query["carrier_id"] = ObjectId(carrier_id)
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self.delivery_zones_collection.find(query)
        zones = []
        async for doc in cursor:
            zones.append(DeliveryZone(**doc))

        return zones

    async def update_delivery_zone(self, zone_id: str, update_data: DeliveryZoneUpdate) -> Optional[DeliveryZone]:
        """Update a delivery zone"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if not update_dict:
            return await self.get_delivery_zone(zone_id)

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.delivery_zones_collection.find_one_and_update(
            {"_id": ObjectId(zone_id)},
            {"$set": update_dict},
            return_document=True
        )

        return DeliveryZone(**result) if result else None

    async def calculate_shipping_costs(
        self,
        origin_country: str,
        destination_country: str,
        weight: float,
        carrier_id: Optional[str] = None,
        destination_region: Optional[str] = None
    ) -> List[ShippingCostQuote]:
        """Calculate shipping costs for given parameters"""
        query = {
            "origin_country": origin_country,
            "destination_country": destination_country,
            "is_active": True,
            "weight_min": {"$lte": weight}
        }

        if carrier_id:
            query["carrier_id"] = ObjectId(carrier_id)

        if destination_region:
            query["$or"] = [
                {"destination_regions": []},  # Applies to all regions
                {"destination_regions": destination_region}
            ]

        # Get matching zones
        cursor = self.delivery_zones_collection.find(query)
        zones = []
        async for doc in cursor:
            zone = DeliveryZone(**doc)
            # Check max weight
            if zone.weight_max is None or weight <= zone.weight_max:
                zones.append(zone)

        # Calculate costs and create quotes
        quotes = []
        for zone in zones:
            try:
                cost = zone.calculate_cost(weight)

                # Get carrier info
                carrier = await self.get_carrier(str(zone.carrier_id))
                if not carrier:
                    continue

                quote = ShippingCostQuote(
                    carrier_id=str(carrier.id),
                    carrier_name=carrier.name,
                    delivery_zone_id=str(zone.id),
                    cost=cost,
                    estimated_days_min=zone.estimated_days_min,
                    estimated_days_max=zone.estimated_days_max
                )
                quotes.append(quote)
            except ValueError as e:
                logger.warning(f"Failed to calculate cost for zone {zone.id}: {e}")
                continue

        # Sort by cost (lowest first)
        quotes.sort(key=lambda q: q.cost)

        return quotes

    # Shipment Operations

    def _generate_shipment_number(self) -> str:
        """Generate a unique shipment number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"SHP-{timestamp}-{random_suffix}"

    async def create_shipment(self, shipment_data: ShipmentCreate) -> Shipment:
        """Create a new shipment"""
        # Generate shipment number
        shipment_number = self._generate_shipment_number()

        # Create shipment
        shipment = Shipment(
            order_id=ObjectId(shipment_data.order_id),
            shipment_number=shipment_number,
            carrier_id=ObjectId(shipment_data.carrier_id),
            tracking_number=shipment_data.tracking_number,
            origin=shipment_data.origin,
            destination=shipment_data.destination,
            package_details=shipment_data.package_details,
            warehouse_id=ObjectId(shipment_data.warehouse_id) if shipment_data.warehouse_id else None,
            delivery_zone_id=ObjectId(shipment_data.delivery_zone_id) if shipment_data.delivery_zone_id else None
        )

        # Calculate shipping cost if delivery zone provided
        if shipment_data.delivery_zone_id:
            zone = await self.get_delivery_zone(shipment_data.delivery_zone_id)
            if zone:
                try:
                    shipment.shipping_cost = zone.calculate_cost(shipment_data.package_details.weight)
                    # Calculate estimated delivery date
                    avg_days = (zone.estimated_days_min + zone.estimated_days_max) / 2
                    shipment.estimated_delivery_date = datetime.utcnow() + timedelta(days=avg_days)
                except ValueError as e:
                    logger.warning(f"Failed to calculate shipping cost: {e}")

        result = await self.shipments_collection.insert_one(
            shipment.model_dump(by_alias=True, exclude={"id"})
        )

        shipment.id = result.inserted_id

        # Create initial tracking event
        await self.add_tracking_event(TrackingEventCreate(
            shipment_id=str(shipment.id),
            status=ShipmentStatus.PENDING,
            description={
                "en": "Shipment created",
                "ko": "배송이 생성되었습니다"
            }
        ))

        logger.info(f"Created shipment: {shipment_number} for order {shipment_data.order_id}")
        return shipment

    async def get_shipment(self, shipment_id: str) -> Optional[Shipment]:
        """Get a shipment by ID"""
        doc = await self.shipments_collection.find_one({"_id": ObjectId(shipment_id)})
        return Shipment(**doc) if doc else None

    async def get_shipment_by_number(self, shipment_number: str) -> Optional[Shipment]:
        """Get a shipment by shipment number"""
        doc = await self.shipments_collection.find_one({"shipment_number": shipment_number})
        return Shipment(**doc) if doc else None

    async def list_shipments(
        self,
        order_id: Optional[str] = None,
        status: Optional[ShipmentStatus] = None,
        carrier_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Shipment], int]:
        """List shipments with filters"""
        query = {}

        if order_id:
            query["order_id"] = ObjectId(order_id)
        if status:
            query["status"] = status
        if carrier_id:
            query["carrier_id"] = ObjectId(carrier_id)

        # Get total count
        total = await self.shipments_collection.count_documents(query)

        # Get paginated results
        cursor = self.shipments_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        shipments = []
        async for doc in cursor:
            shipments.append(Shipment(**doc))

        return shipments, total

    async def update_shipment(self, shipment_id: str, update_data: ShipmentUpdate) -> Optional[Shipment]:
        """Update a shipment"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if not update_dict:
            return await self.get_shipment(shipment_id)

        # Handle special fields
        if "carrier_id" in update_dict:
            update_dict["carrier_id"] = ObjectId(update_dict["carrier_id"])

        # Update timestamps based on status
        if "status" in update_dict:
            if update_dict["status"] == ShipmentStatus.PICKED_UP:
                update_dict["shipped_at"] = datetime.utcnow()
            elif update_dict["status"] == ShipmentStatus.DELIVERED:
                update_dict["delivered_at"] = datetime.utcnow()
                if "actual_delivery_date" not in update_dict:
                    update_dict["actual_delivery_date"] = datetime.utcnow()

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.shipments_collection.find_one_and_update(
            {"_id": ObjectId(shipment_id)},
            {"$set": update_dict},
            return_document=True
        )

        if result:
            # Update order tracking info if status changed
            if "status" in update_dict or "tracking_number" in update_dict:
                await self._update_order_tracking(result)

        return Shipment(**result) if result else None

    async def delete_shipment(self, shipment_id: str) -> bool:
        """Delete a shipment (soft delete recommended in production)"""
        result = await self.shipments_collection.delete_one({"_id": ObjectId(shipment_id)})
        return result.deleted_count > 0

    async def _update_order_tracking(self, shipment_doc: dict):
        """Update order with tracking information"""
        try:
            carrier = await self.get_carrier(str(shipment_doc["carrier_id"]))
            carrier_name = carrier.name.get("en", "") if carrier else ""

            update_data = {
                "tracking_number": shipment_doc.get("tracking_number"),
                "carrier": carrier_name,
                "updated_at": datetime.utcnow()
            }

            # Update dates based on shipment status
            if shipment_doc.get("shipped_at"):
                update_data["shipped_at"] = shipment_doc["shipped_at"]
            if shipment_doc.get("delivered_at"):
                update_data["delivered_at"] = shipment_doc["delivered_at"]
            if shipment_doc.get("estimated_delivery_date"):
                update_data["estimated_delivery_date"] = shipment_doc["estimated_delivery_date"]
            if shipment_doc.get("actual_delivery_date"):
                update_data["actual_delivery_date"] = shipment_doc["actual_delivery_date"]

            # Update order status if delivered
            if shipment_doc["status"] == ShipmentStatus.DELIVERED:
                update_data["status"] = "completed"

            await self.orders_collection.update_one(
                {"_id": shipment_doc["order_id"]},
                {"$set": update_data}
            )
        except Exception as e:
            logger.error(f"Failed to update order tracking: {e}")

    # Tracking Event Operations

    async def add_tracking_event(self, event_data: TrackingEventCreate) -> TrackingEvent:
        """Add a tracking event"""
        event = TrackingEvent(
            shipment_id=ObjectId(event_data.shipment_id),
            status=event_data.status,
            location=event_data.location,
            description=event_data.description,
            event_time=event_data.event_time or datetime.utcnow()
        )

        result = await self.tracking_events_collection.insert_one(
            event.model_dump(by_alias=True, exclude={"id"})
        )

        event.id = result.inserted_id

        # Update shipment status
        await self.update_shipment(
            event_data.shipment_id,
            ShipmentUpdate(status=event_data.status)
        )

        logger.info(f"Added tracking event for shipment {event_data.shipment_id}: {event_data.status}")
        return event

    async def get_tracking_events(self, shipment_id: str) -> List[TrackingEvent]:
        """Get all tracking events for a shipment"""
        cursor = self.tracking_events_collection.find(
            {"shipment_id": ObjectId(shipment_id)}
        ).sort("event_time", -1)

        events = []
        async for doc in cursor:
            events.append(TrackingEvent(**doc))

        return events

    # Statistics

    async def get_logistics_stats(self) -> Dict:
        """Get logistics statistics"""
        # Shipment counts by status
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        status_counts = {status: 0 for status in ShipmentStatus}
        async for doc in self.shipments_collection.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]

        total_shipments = sum(status_counts.values())

        # Count carriers
        total_carriers = await self.carriers_collection.count_documents({})
        active_carriers = await self.carriers_collection.count_documents({"is_active": True})

        # Count delivery zones
        total_delivery_zones = await self.delivery_zones_collection.count_documents({})

        return {
            "total_shipments": total_shipments,
            "pending_shipments": status_counts.get(ShipmentStatus.PENDING, 0),
            "in_transit_shipments": (
                status_counts.get(ShipmentStatus.PICKED_UP, 0) +
                status_counts.get(ShipmentStatus.IN_TRANSIT, 0) +
                status_counts.get(ShipmentStatus.OUT_FOR_DELIVERY, 0)
            ),
            "delivered_shipments": status_counts.get(ShipmentStatus.DELIVERED, 0),
            "failed_shipments": status_counts.get(ShipmentStatus.FAILED, 0) + status_counts.get(ShipmentStatus.RETURNED, 0),
            "total_carriers": total_carriers,
            "active_carriers": active_carriers,
            "total_delivery_zones": total_delivery_zones
        }
