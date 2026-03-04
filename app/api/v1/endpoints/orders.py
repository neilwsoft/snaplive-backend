"""Orders API Endpoints

API routes for order management operations.
"""

import random
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError

from app.database import get_database
from app.services.order_service import OrderService
from app.models.order import Order, OrderStatus, PaymentStatus, Platform, OrderItem, ShippingAddress
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderListResponse,
    OrderItemSchema,
    ShippingAddressSchema,
    ProductBadgeSchema,
)
from pydantic import BaseModel


router = APIRouter()


def get_order_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> OrderService:
    """Dependency to get order service"""
    return OrderService(db)


# Stats Response Schema
class OrderStatsResponse(BaseModel):
    """Response model for order statistics"""
    total_orders: int
    status_counts: dict
    payment_status_counts: dict
    platform_counts: dict
    total_revenue: float
    average_order_value: float
    orders_last_30_days: int
    daily_orders: List[dict]
    daily_orders_by_platform: List[dict]
    pending_orders: int
    confirmed_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int


# Order CRUD Endpoints

def build_order_response(order: Order) -> OrderResponse:
    """Helper to build OrderResponse from Order model"""
    return OrderResponse(
        id=str(order.id),
        order_number=order.order_number,
        buyer_email=order.buyer_email,
        buyer_name=order.buyer_name,
        buyer_language=order.buyer_language,
        buyer_avatar_url=getattr(order, 'buyer_avatar_url', None),
        buyer_phone=getattr(order, 'buyer_phone', None),
        live_simulcast_id=getattr(order, 'live_simulcast_id', None),
        items=[OrderItemSchema(**item) if isinstance(item, dict) else OrderItemSchema(**item.model_dump()) for item in order.items],
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee,
        tax=order.tax,
        total=order.total,
        currency=order.currency,
        status=order.status,
        payment_status=order.payment_status,
        platform=order.platform,
        platform_order_id=order.platform_order_id,
        shipping_address=ShippingAddressSchema(**order.shipping_address.model_dump()) if hasattr(order.shipping_address, 'model_dump') else ShippingAddressSchema(**order.shipping_address),
        tracking_number=order.tracking_number,
        carrier=order.carrier,
        estimated_delivery_date=order.estimated_delivery_date,
        actual_delivery_date=order.actual_delivery_date,
        buyer_notes=order.buyer_notes,
        seller_notes=order.seller_notes,
        processing_step=getattr(order, 'processing_step', 1),
        created_at=order.created_at,
        updated_at=order.updated_at,
        confirmed_at=order.confirmed_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        cancelled_at=order.cancelled_at
    )


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    service: OrderService = Depends(get_order_service)
):
    """Create a new order"""

    # Calculate subtotal and total
    subtotal = sum(item.subtotal for item in order_data.items)
    total = subtotal + order_data.shipping_fee + order_data.tax

    # Generate unique order number
    order_number = f"B{datetime.utcnow().strftime('%Y%m%d')}{random.randint(100000000, 999999999)}"

    # Create Order model
    order = Order(
        order_number=order_number,
        buyer_email=order_data.buyer_email,
        buyer_name=order_data.buyer_name,
        buyer_language=order_data.buyer_language,
        buyer_avatar_url=order_data.buyer_avatar_url,
        buyer_phone=order_data.buyer_phone,
        live_simulcast_id=order_data.live_simulcast_id,
        items=[item.model_dump() for item in order_data.items],
        subtotal=subtotal,
        shipping_fee=order_data.shipping_fee,
        tax=order_data.tax,
        total=total,
        currency=order_data.currency,
        platform=order_data.platform,
        platform_order_id=order_data.platform_order_id,
        shipping_address=order_data.shipping_address.model_dump(),
        buyer_notes=order_data.buyer_notes
    )

    created_order = await service.create_order(order)
    return build_order_response(created_order)


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    status: Optional[OrderStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    platform: Optional[Platform] = Query(None),
    buyer_email: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by order number or buyer name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: OrderService = Depends(get_order_service)
):
    """Get all orders with filtering and pagination"""
    orders, total = await service.get_orders(
        status=status,
        payment_status=payment_status,
        platform=platform,
        buyer_email=buyer_email,
        search=search,
        page=page,
        page_size=page_size
    )

    order_responses = [build_order_response(order) for order in orders]

    return OrderListResponse(
        orders=order_responses,
        total=total,
        page=page,
        page_size=page_size
    )


# Statistics Endpoint - Must come before /{order_id} to avoid path conflicts

@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    service: OrderService = Depends(get_order_service)
):
    """Get comprehensive order statistics"""
    stats = await service.get_order_stats()
    return OrderStatsResponse(**stats)


# Monthly Revenue Stats Response Schema
class MonthlyRevenueItem(BaseModel):
    """Single month revenue data"""
    month: str
    month_label: str
    revenue: float
    cost: float
    order_count: int


class MonthlyRevenueStatsResponse(BaseModel):
    """Response model for monthly revenue statistics"""
    monthly_data: List[MonthlyRevenueItem]
    current_month_revenue: float
    previous_month_revenue: float
    percentage_change: float
    total_revenue: float


@router.get("/stats/revenue", response_model=MonthlyRevenueStatsResponse)
async def get_revenue_stats(
    months: int = Query(5, ge=1, le=12, description="Number of months to return"),
    service: OrderService = Depends(get_order_service)
):
    """
    Get monthly revenue statistics for dashboard.

    Returns revenue breakdown by month with comparison metrics.
    Used by the RevenueWidget component.
    """
    stats = await service.get_monthly_revenue_stats(months)
    return MonthlyRevenueStatsResponse(**stats)


# Seed Response Schema
class SeedOrdersResponse(BaseModel):
    """Response model for order seeding"""
    message: str
    count: int
    orders_created: List[str]


@router.post("/seed", response_model=SeedOrdersResponse)
async def seed_orders(
    count: int = Query(20, ge=1, le=100, description="Number of orders to create"),
    clear_existing: bool = Query(False, description="Clear existing orders before seeding"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Seed database with dummy orders for testing"""
    service = OrderService(db)

    # Optionally clear existing orders
    if clear_existing:
        await db.orders.delete_many({})

    # Chinese buyer names with English nicknames (matching frontend mock data style)
    buyers = [
        {"name": "Annie 安安", "email": "annie@example.cn", "phone": "+86 138 1234 5678", "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop"},
        {"name": "The Product Curator 品管官", "email": "curator@example.cn", "phone": "+86 139 8765 4321", "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop"},
        {"name": "Easy Pesl 易凯", "email": "easypesl@example.cn", "phone": "+86 135 5555 6666", "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop"},
        {"name": "Sincere Sarah 心心", "email": "sarah@example.cn", "phone": "+86 136 7777 8888", "avatar": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop"},
        {"name": "Honest Hank 老实", "email": "hank@example.cn", "phone": "+86 137 9999 0000", "avatar": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop"},
        {"name": "Dot Com 嚣嚣", "email": "dotcom@example.cn", "phone": "+86 138 1111 2222", "avatar": None},
        {"name": "Best Price Ben 好价", "email": "ben@example.cn", "phone": "+86 139 3333 4444", "avatar": None},
        {"name": "Treasure Ted 寻宝", "email": "ted@example.cn", "phone": "+86 135 5555 6666", "avatar": None},
        {"name": "Rapid Rob 罗罗", "email": "rob@example.cn", "phone": "+86 136 7777 8888", "avatar": None},
        {"name": "Beauty Queen 美美", "email": "beauty@example.cn", "phone": "+86 137 9999 0000", "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop"},
    ]

    # Product data for orders
    products = [
        {"name": {"en": "Velvet Matte Lipstick", "ko": "벨벳 매트 립스틱"}, "sku": "90071-M-NU002", "price": 89.00, "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=200&h=200&fit=crop", "badges": [{"type": "new", "label": "NEW"}]},
        {"name": {"en": "Bright Yellow Knitted Long Sleeve Dress", "ko": "밝은 노란색 니트 롱슬리브 드레스"}, "sku": "104850-L-BL", "price": 299.00, "image": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=200&h=200&fit=crop", "badges": [{"type": "new", "label": "NEW"}, {"type": "bestseller", "label": "BESTSELLER"}]},
        {"name": {"en": "PRO-Vlog Wireless Mic System", "ko": "프로-블로그 무선 마이크 시스템"}, "sku": "77800-PRO-BK", "price": 599.00, "image": "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=200&h=200&fit=crop", "badges": [{"type": "new", "label": "NEW"}]},
        {"name": {"en": "Hydrating Face Serum", "ko": "수분 페이스 세럼"}, "sku": "50021-FS-30ML", "price": 129.00, "image": "https://images.unsplash.com/photo-1617897903246-719242758050?w=200&h=200&fit=crop", "badges": [{"type": "bestseller", "label": "BESTSELLER"}]},
        {"name": {"en": "Silk Blend Scarf", "ko": "실크 블렌드 스카프"}, "sku": "88320-SC-RD", "price": 159.00, "image": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=200&h=200&fit=crop", "badges": []},
        {"name": {"en": "LED Ring Light Kit", "ko": "LED 링 라이트 키트"}, "sku": "66100-RL-18", "price": 249.00, "image": "https://images.unsplash.com/photo-1582053433976-25c00369fc93?w=200&h=200&fit=crop", "badges": [{"type": "hot-seller", "label": "HOT"}]},
        {"name": {"en": "Vitamin C Brightening Cream", "ko": "비타민 C 브라이트닝 크림"}, "sku": "50089-VC-50G", "price": 179.00, "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=200&h=200&fit=crop", "badges": []},
        {"name": {"en": "Bluetooth Earbuds Pro", "ko": "블루투스 이어버드 프로"}, "sku": "77500-EB-WH", "price": 199.00, "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=200&h=200&fit=crop", "badges": [{"type": "new", "label": "NEW"}]},
    ]

    # Platforms
    platforms = [Platform.DOUYIN, Platform.XIAOHONGSHU, Platform.TAOBAO, Platform.SNAPLIVE]

    # Statuses with weighted distribution
    statuses = [
        (OrderStatus.PENDING, 3),
        (OrderStatus.READY, 2),
        (OrderStatus.SHOPPING, 2),
        (OrderStatus.SHIPPED, 2),
        (OrderStatus.DELIVERED, 4),
        (OrderStatus.CANCELLED, 1),
        (OrderStatus.RETURNING, 2),
        (OrderStatus.RETURN, 1),
    ]
    status_weights = [w for _, w in statuses]
    status_choices = [s for s, _ in statuses]

    # Cities for shipping addresses
    cities = [
        {"city": "北京", "province": "北京市", "postal": "100000"},
        {"city": "上海", "province": "上海市", "postal": "200000"},
        {"city": "广州", "province": "广东省", "postal": "510000"},
        {"city": "深圳", "province": "广东省", "postal": "518000"},
        {"city": "杭州", "province": "浙江省", "postal": "310000"},
        {"city": "成都", "province": "四川省", "postal": "610000"},
    ]

    created_order_ids = []

    for i in range(count):
        # Random buyer
        buyer = random.choice(buyers)

        # Random products (1-4)
        num_products = random.randint(1, 4)
        selected_products = random.sample(products, min(num_products, len(products)))

        items = []
        subtotal = 0.0
        for prod in selected_products:
            qty = random.randint(1, 3)
            item_subtotal = prod["price"] * qty
            subtotal += item_subtotal
            items.append({
                "product_name": prod["name"],
                "sku": prod["sku"],
                "quantity": qty,
                "unit_price": prod["price"],
                "subtotal": item_subtotal,
                "image_url": prod["image"],
                "unit": "pcs",
                "fulfillment_status": None,
                "badges": prod["badges"]
            })

        # Calculate totals
        shipping_fee = random.choice([0, 15, 25, 35])
        tax = round(subtotal * 0.06, 2)
        total = round(subtotal + shipping_fee + tax, 2)

        # Random city
        city_data = random.choice(cities)

        # Random status
        status = random.choices(status_choices, weights=status_weights, k=1)[0]

        # Random platform
        platform = random.choice(platforms)

        # Random time (last 7 days)
        hours_ago = random.randint(1, 168)  # Up to 7 days
        created_at = datetime.utcnow() - timedelta(hours=hours_ago)

        # Generate order number
        order_number = f"B{created_at.strftime('%Y%m%d')}{random.randint(100000000, 999999999)}"

        # Live simulcast ID
        live_simulcast_id = f"LIVE-{random.randint(1000, 9999):04X}-{random.randint(1000, 9999):04X}-{random.randint(1000, 9999):04X}"

        # Create order
        order = Order(
            order_number=order_number,
            buyer_email=buyer["email"],
            buyer_name=buyer["name"],
            buyer_language=random.choice(["ko", "zh"]),
            buyer_avatar_url=buyer["avatar"],
            buyer_phone=buyer["phone"],
            live_simulcast_id=live_simulcast_id,
            items=items,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            total=total,
            currency="CNY",
            status=status,
            payment_status=PaymentStatus.COMPLETED if status not in [OrderStatus.CANCELLED, OrderStatus.PENDING] else PaymentStatus.PENDING,
            platform=platform,
            platform_order_id=f"{platform.value.upper()}-{random.randint(10000000, 99999999)}",
            shipping_address=ShippingAddress(
                recipient_name=buyer["name"],
                phone=buyer["phone"],
                address_line1=f"{random.randint(1, 999)}号 {random.choice(['中山路', '南京路', '淮海路', '人民路', '解放路'])}",
                address_line2=f"{random.choice(['A', 'B', 'C'])}栋 {random.randint(1, 30)}层 {random.randint(1, 20)}室",
                city=city_data["city"],
                province=city_data["province"],
                postal_code=city_data["postal"],
                country="中国"
            ),
            processing_step=2 if status in [OrderStatus.READY, OrderStatus.SHIPPED, OrderStatus.DELIVERED] else 1,
            created_at=created_at,
            updated_at=created_at,
            shipped_at=created_at + timedelta(hours=random.randint(1, 24)) if status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED] else None,
            delivered_at=created_at + timedelta(hours=random.randint(24, 72)) if status == OrderStatus.DELIVERED else None,
        )

        created_order = await service.create_order(order)
        created_order_ids.append(str(created_order.id))

    return SeedOrdersResponse(
        message=f"Successfully seeded {count} orders",
        count=count,
        orders_created=created_order_ids
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Get an order by ID"""
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return build_order_response(order)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    service: OrderService = Depends(get_order_service)
):
    """Update an order"""
    update_dict = update_data.model_dump(exclude_unset=True)

    # Handle items update - convert to dict format
    if 'items' in update_dict and update_dict['items'] is not None:
        update_dict['items'] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_dict['items']]

    updated_order = await service.update_order(order_id, update_dict)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")

    return build_order_response(updated_order)


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: str,
    service: OrderService = Depends(get_order_service)
):
    """Delete an order"""
    success = await service.delete_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")


# Order Processing Endpoint

class OrderProcessingRequest(BaseModel):
    """Request model for order processing"""
    goods_details: dict  # {products, total_quantity, total_declared_value, currency, gross_weight, number_of_packages}
    shipper: dict  # {name, contact_number, email, dispatch_address}
    recipient: dict  # {name, contact_number, email, dispatch_address}
    waybill: dict  # {logistics_provider, live_hub_order_id, marketplace_order_id, marketplace, shipping_service_type}
    notes: Optional[dict] = None  # {payment_method, delivery_instructions, remarks_insurance}


class OrderProcessingResponse(BaseModel):
    """Response model for order processing"""
    success: bool
    order_id: str
    tracking_number: Optional[str]
    carrier: str
    status: str
    message: str


@router.post("/{order_id}/process", response_model=OrderProcessingResponse)
async def process_order(
    order_id: str,
    processing_data: OrderProcessingRequest,
    service: OrderService = Depends(get_order_service)
):
    """
    Process an order with shipping details.
    This is the final step after selecting products (step 1) and filling shipping form (step 2).
    """
    try:
        # Get existing order
        order = await service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Validate order is in a processable state
        if order.status not in [OrderStatus.PENDING, OrderStatus.READY]:
            raise HTTPException(
                status_code=400,
                detail=f"Order cannot be processed in status: {order.status}"
            )

        # Validate required fields
        if not processing_data.shipper or not processing_data.shipper.get("name"):
            raise HTTPException(status_code=400, detail="Shipper name is required")
        if not processing_data.recipient or not processing_data.recipient.get("name"):
            raise HTTPException(status_code=400, detail="Recipient name is required")
        if not processing_data.waybill or not processing_data.waybill.get("logistics_provider"):
            raise HTTPException(status_code=400, detail="Logistics provider is required")

        # Generate tracking number
        carrier = processing_data.waybill.get("logistics_provider", "unknown")
        tracking_number = f"{carrier.upper()}-{datetime.utcnow().strftime('%Y%m%d')}{random.randint(100000000, 999999999)}"

        # Update order with shipping details
        update_dict = {
            "status": OrderStatus.READY.value,
            "carrier": carrier,
            "tracking_number": tracking_number,
            "processing_step": 2,
            "seller_notes": processing_data.notes.get("delivery_instructions", "") if processing_data.notes else "",
            "updated_at": datetime.utcnow(),
        }

        # Update shipping address if recipient info is different
        if processing_data.recipient:
            update_dict["shipping_address"] = {
                "recipient_name": processing_data.recipient.get("name", order.shipping_address.recipient_name),
                "phone": processing_data.recipient.get("contact_number", order.shipping_address.phone),
                "address_line1": processing_data.recipient.get("dispatch_address", order.shipping_address.address_line1),
                "address_line2": order.shipping_address.address_line2 if hasattr(order.shipping_address, 'address_line2') else "",
                "city": order.shipping_address.city,
                "province": order.shipping_address.province,
                "postal_code": order.shipping_address.postal_code,
                "country": order.shipping_address.country,
            }

        updated_order = await service.update_order(order_id, update_dict)
        if not updated_order:
            raise HTTPException(status_code=500, detail="Failed to update order")

        return OrderProcessingResponse(
            success=True,
            order_id=str(updated_order.id),
            tracking_number=tracking_number,
            carrier=carrier,
            status=str(updated_order.status),
            message="Order processed successfully. Ready to ship."
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "processing_data": {
                "goods_details": str(processing_data.goods_details),
                "shipper": str(processing_data.shipper),
                "recipient": str(processing_data.recipient),
                "waybill": str(processing_data.waybill),
            }
        }
        print(f"Error processing order: {error_details}")
        raise HTTPException(
            status_code=400,
            detail=f"Error processing order: {str(e)}"
        )
