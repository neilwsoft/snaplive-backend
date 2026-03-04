"""Logistics API Endpoints

API routes for logistics management operations.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.services.logistics_service import LogisticsService
from app.utils.qr_generator import generate_tracking_qr
from app.utils.label_generator import generate_shipping_label
from app.models.logistics import ShipmentStatus
from app.scripts.seed_logistics import seed_logistics_database
from app.schemas.logistics import (
    # Carrier schemas
    CarrierCreate,
    CarrierUpdate,
    CarrierResponse,
    # Delivery zone schemas
    DeliveryZoneCreate,
    DeliveryZoneUpdate,
    DeliveryZoneResponse,
    CalculateShippingCostRequest,
    CalculateShippingCostResponse,
    # Shipment schemas
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ShipmentListResponse,
    # Tracking schemas
    TrackingEventCreate,
    TrackingEventResponse,
    TrackingEventListResponse,
    # QR and label schemas
    GenerateQRCodeRequest,
    GenerateQRCodeResponse,
    GenerateLabelRequest,
    GenerateLabelResponse,
    # Stats
    LogisticsStatsResponse
)

router = APIRouter()


def get_logistics_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> LogisticsService:
    """Dependency to get logistics service"""
    return LogisticsService(db)


# Carrier Endpoints

@router.post("/carriers", response_model=CarrierResponse, status_code=201)
async def create_carrier(
    carrier_data: CarrierCreate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Create a new carrier"""
    carrier = await service.create_carrier(carrier_data)
    return CarrierResponse(
        _id=str(carrier.id),
        **carrier.model_dump(exclude={"id"})
    )


@router.get("/carriers", response_model=List[CarrierResponse])
async def list_carriers(
    is_active: Optional[bool] = Query(None),
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get all carriers"""
    carriers = await service.list_carriers(is_active=is_active)
    return [
        CarrierResponse(_id=str(c.id), **c.model_dump(exclude={"id"}))
        for c in carriers
    ]


@router.get("/carriers/{carrier_id}", response_model=CarrierResponse)
async def get_carrier(
    carrier_id: str,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get a carrier by ID"""
    carrier = await service.get_carrier(carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    return CarrierResponse(
        _id=str(carrier.id),
        **carrier.model_dump(exclude={"id"})
    )


@router.patch("/carriers/{carrier_id}", response_model=CarrierResponse)
async def update_carrier(
    carrier_id: str,
    update_data: CarrierUpdate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Update a carrier"""
    carrier = await service.update_carrier(carrier_id, update_data)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    return CarrierResponse(
        _id=str(carrier.id),
        **carrier.model_dump(exclude={"id"})
    )


# Delivery Zone Endpoints

@router.post("/delivery-zones", response_model=DeliveryZoneResponse, status_code=201)
async def create_delivery_zone(
    zone_data: DeliveryZoneCreate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Create a new delivery zone"""
    zone = await service.create_delivery_zone(zone_data)

    # Get carrier for response
    carrier = await service.get_carrier(str(zone.carrier_id))

    return DeliveryZoneResponse(
        _id=str(zone.id),
        carrier_id=str(zone.carrier_id),
        carrier_name=carrier.name if carrier else None,
        **zone.model_dump(exclude={"id", "carrier_id"})
    )


@router.get("/delivery-zones", response_model=List[DeliveryZoneResponse])
async def list_delivery_zones(
    carrier_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get all delivery zones"""
    zones = await service.list_delivery_zones(carrier_id=carrier_id, is_active=is_active)

    # Get carrier names
    carrier_map = {}
    if zones:
        carriers = await service.list_carriers()
        carrier_map = {str(c.id): c.name for c in carriers}

    return [
        DeliveryZoneResponse(
            _id=str(z.id),
            carrier_id=str(z.carrier_id),
            carrier_name=carrier_map.get(str(z.carrier_id)),
            **z.model_dump(exclude={"id", "carrier_id"})
        )
        for z in zones
    ]


@router.post("/delivery-zones/calculate-cost", response_model=CalculateShippingCostResponse)
async def calculate_shipping_cost(
    request: CalculateShippingCostRequest,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Calculate shipping cost for given parameters"""
    quotes = await service.calculate_shipping_costs(
        origin_country=request.origin_country,
        destination_country=request.destination_country,
        weight=request.weight,
        carrier_id=request.carrier_id,
        destination_region=request.destination_region
    )

    return CalculateShippingCostResponse(quotes=quotes)


@router.get("/delivery-zones/{zone_id}", response_model=DeliveryZoneResponse)
async def get_delivery_zone(
    zone_id: str,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get a delivery zone by ID"""
    zone = await service.get_delivery_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Delivery zone not found")

    # Get carrier
    carrier = await service.get_carrier(str(zone.carrier_id))

    return DeliveryZoneResponse(
        _id=str(zone.id),
        carrier_id=str(zone.carrier_id),
        carrier_name=carrier.name if carrier else None,
        **zone.model_dump(exclude={"id", "carrier_id"})
    )


@router.patch("/delivery-zones/{zone_id}", response_model=DeliveryZoneResponse)
async def update_delivery_zone(
    zone_id: str,
    update_data: DeliveryZoneUpdate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Update a delivery zone"""
    zone = await service.update_delivery_zone(zone_id, update_data)
    if not zone:
        raise HTTPException(status_code=404, detail="Delivery zone not found")

    # Get carrier
    carrier = await service.get_carrier(str(zone.carrier_id))

    return DeliveryZoneResponse(
        _id=str(zone.id),
        carrier_id=str(zone.carrier_id),
        carrier_name=carrier.name if carrier else None,
        **zone.model_dump(exclude={"id", "carrier_id"})
    )


# Shipment Endpoints

@router.post("/shipments", response_model=ShipmentResponse, status_code=201)
async def create_shipment(
    shipment_data: ShipmentCreate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Create a new shipment"""
    try:
        shipment = await service.create_shipment(shipment_data)

        # Get carrier for response
        carrier = await service.get_carrier(str(shipment.carrier_id))

        return ShipmentResponse(
            _id=str(shipment.id),
            order_id=str(shipment.order_id),
            carrier_id=str(shipment.carrier_id),
            carrier_name=carrier.name if carrier else None,
            warehouse_id=str(shipment.warehouse_id) if shipment.warehouse_id else None,
            delivery_zone_id=str(shipment.delivery_zone_id) if shipment.delivery_zone_id else None,
            is_delivered=shipment.is_delivered,
            is_in_transit=shipment.is_in_transit,
            is_pending=shipment.is_pending,
            **shipment.model_dump(exclude={"id", "order_id", "carrier_id", "warehouse_id", "delivery_zone_id"})
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shipments", response_model=ShipmentListResponse)
async def list_shipments(
    order_id: Optional[str] = Query(None),
    status: Optional[ShipmentStatus] = Query(None),
    carrier_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: LogisticsService = Depends(get_logistics_service)
):
    """List shipments with filters and pagination"""
    skip = (page - 1) * page_size

    shipments, total = await service.list_shipments(
        order_id=order_id,
        status=status,
        carrier_id=carrier_id,
        skip=skip,
        limit=page_size
    )

    # Get carrier names for responses
    carrier_map = {}
    if shipments:
        carriers = await service.list_carriers()
        carrier_map = {str(c.id): c.name for c in carriers}

    shipment_responses = []
    for shipment in shipments:
        shipment_responses.append(
            ShipmentResponse(
                _id=str(shipment.id),
                order_id=str(shipment.order_id),
                carrier_id=str(shipment.carrier_id),
                carrier_name=carrier_map.get(str(shipment.carrier_id)),
                warehouse_id=str(shipment.warehouse_id) if shipment.warehouse_id else None,
                delivery_zone_id=str(shipment.delivery_zone_id) if shipment.delivery_zone_id else None,
                is_delivered=shipment.is_delivered,
                is_in_transit=shipment.is_in_transit,
                is_pending=shipment.is_pending,
                **shipment.model_dump(exclude={"id", "order_id", "carrier_id", "warehouse_id", "delivery_zone_id"})
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return ShipmentListResponse(
        items=shipment_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# Statistics (must come before /{shipment_id} to avoid route conflicts)

@router.get("/shipments/stats", response_model=LogisticsStatsResponse)
async def get_logistics_stats(
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get logistics statistics"""
    stats = await service.get_logistics_stats()
    return LogisticsStatsResponse(**stats)


# QR Code and Label Generation (must come before /{shipment_id} to avoid route conflicts)

@router.post("/shipments/generate-qr", response_model=GenerateQRCodeResponse)
async def generate_qr_code(
    request: GenerateQRCodeRequest,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Generate QR code for a shipment"""
    shipment = await service.get_shipment(request.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Generate QR code
    qr_code_url = generate_tracking_qr(
        shipment_id=request.shipment_id,
        tracking_number=shipment.tracking_number or shipment.shipment_number,
        size=request.size,
        format=request.format
    )

    # Update shipment with QR code URL
    await service.update_shipment(
        request.shipment_id,
        ShipmentUpdate(qr_code_url=qr_code_url)
    )

    return GenerateQRCodeResponse(
        qr_code_url=qr_code_url,
        shipment_id=request.shipment_id
    )


@router.post("/shipments/generate-label", response_model=GenerateLabelResponse)
async def generate_label(
    request: GenerateLabelRequest,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Generate shipping label PDF for a shipment"""
    shipment = await service.get_shipment(request.shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get carrier
    carrier = await service.get_carrier(str(shipment.carrier_id))
    carrier_name = carrier.name.get("en", "") if carrier else "Unknown Carrier"

    # Generate label
    label_url = generate_shipping_label(
        shipment_number=shipment.shipment_number,
        tracking_number=shipment.tracking_number,
        carrier_name=carrier_name,
        origin=shipment.origin.model_dump(),
        destination=shipment.destination.model_dump(),
        package_details=shipment.package_details.model_dump(),
        qr_code_data_url=shipment.qr_code_url
    )

    # Update shipment with label URL
    await service.update_shipment(
        request.shipment_id,
        ShipmentUpdate(label_url=label_url)
    )

    return GenerateLabelResponse(
        label_url=label_url,
        shipment_id=request.shipment_id
    )


# Tracking Events (must come before /{shipment_id} to avoid route conflicts)

@router.post("/shipments/track", response_model=TrackingEventResponse)
async def add_tracking_event(
    event_data: TrackingEventCreate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Add a tracking event to a shipment"""
    try:
        event = await service.add_tracking_event(event_data)

        return TrackingEventResponse(
            _id=str(event.id),
            shipment_id=str(event.shipment_id),
            **event.model_dump(exclude={"id", "shipment_id"})
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Parameterized routes (must come after all specific routes to avoid conflicts)

@router.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: str,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get a shipment by ID"""
    shipment = await service.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get carrier
    carrier = await service.get_carrier(str(shipment.carrier_id))

    return ShipmentResponse(
        _id=str(shipment.id),
        order_id=str(shipment.order_id),
        carrier_id=str(shipment.carrier_id),
        carrier_name=carrier.name if carrier else None,
        warehouse_id=str(shipment.warehouse_id) if shipment.warehouse_id else None,
        delivery_zone_id=str(shipment.delivery_zone_id) if shipment.delivery_zone_id else None,
        is_delivered=shipment.is_delivered,
        is_in_transit=shipment.is_in_transit,
        is_pending=shipment.is_pending,
        **shipment.model_dump(exclude={"id", "order_id", "carrier_id", "warehouse_id", "delivery_zone_id"})
    )


@router.patch("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: str,
    update_data: ShipmentUpdate,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Update a shipment"""
    shipment = await service.update_shipment(shipment_id, update_data)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Get carrier
    carrier = await service.get_carrier(str(shipment.carrier_id))

    return ShipmentResponse(
        _id=str(shipment.id),
        order_id=str(shipment.order_id),
        carrier_id=str(shipment.carrier_id),
        carrier_name=carrier.name if carrier else None,
        warehouse_id=str(shipment.warehouse_id) if shipment.warehouse_id else None,
        delivery_zone_id=str(shipment.delivery_zone_id) if shipment.delivery_zone_id else None,
        is_delivered=shipment.is_delivered,
        is_in_transit=shipment.is_in_transit,
        is_pending=shipment.is_pending,
        **shipment.model_dump(exclude={"id", "order_id", "carrier_id", "warehouse_id", "delivery_zone_id"})
    )


@router.delete("/shipments/{shipment_id}", status_code=204)
async def delete_shipment(
    shipment_id: str,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Delete a shipment"""
    deleted = await service.delete_shipment(shipment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Shipment not found")


@router.get("/shipments/{shipment_id}/tracking-events", response_model=TrackingEventListResponse)
async def get_tracking_events(
    shipment_id: str,
    service: LogisticsService = Depends(get_logistics_service)
):
    """Get tracking history for a shipment"""
    events = await service.get_tracking_events(shipment_id)

    event_responses = [
        TrackingEventResponse(
            _id=str(event.id),
            shipment_id=str(event.shipment_id),
            **event.model_dump(exclude={"id", "shipment_id"})
        )
        for event in events
    ]

    return TrackingEventListResponse(
        items=event_responses,
        total=len(event_responses)
    )


# Database Seeding

@router.post("/seed")
async def seed_database(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Seed the database with sample logistics data"""
    try:
        await seed_logistics_database(db)
        return {"message": "Logistics database seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
