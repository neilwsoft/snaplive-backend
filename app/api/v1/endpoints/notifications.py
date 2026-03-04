"""
Notification endpoints for testing the notification system
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import get_database
from app.config import settings
from app.models.order import Order, OrderItem, ShippingAddress, OrderStatus, Platform
from app.models.notification import NotificationType
from app.schemas.notification import TestNotificationRequest, NotificationResponse, NotificationListResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/test", response_model=dict)
async def test_notification(
    request: TestNotificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Test notification endpoint - sends a test notification email

    This endpoint creates a mock order and sends a notification for testing purposes.
    """
    try:
        # Create a mock order for testing
        mock_order = Order(
            order_number=f"TEST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            buyer_email=request.recipient_email,
            buyer_name=request.recipient_name,
            buyer_language=request.language,
            items=[
                OrderItem(
                    product_name={
                        "ko": "테스트 상품 1",
                        "zh": "测试商品 1"
                    },
                    quantity=2,
                    unit_price=29.99,
                    subtotal=59.98,
                    sku="TEST-SKU-001"
                ),
                OrderItem(
                    product_name={
                        "ko": "테스트 상품 2",
                        "zh": "测试商品 2"
                    },
                    quantity=1,
                    unit_price=49.99,
                    subtotal=49.99,
                    sku="TEST-SKU-002"
                )
            ],
            subtotal=109.97,
            shipping_fee=10.00,
            tax=5.50,
            total=125.47,
            currency="CNY",
            status=OrderStatus.CONFIRMED,
            platform=Platform.TAOBAO,
            platform_order_id="TAOBAO-TEST-12345",
            shipping_address=ShippingAddress(
                recipient_name=request.recipient_name,
                phone="+86-138-0000-0000",
                address_line1="123 Test Street, Building 5, Apt 301",
                address_line2="",
                city="Beijing",
                province="Beijing",
                postal_code="100000",
                country="China"
            ),
            tracking_number="SF1234567890" if request.notification_type in [
                NotificationType.ORDER_SHIPPED,
                NotificationType.ORDER_DELIVERED
            ] else None,
            carrier="SF Express" if request.notification_type in [
                NotificationType.ORDER_SHIPPED,
                NotificationType.ORDER_DELIVERED
            ] else None,
            estimated_delivery_date=datetime.utcnow() + timedelta(days=3) if request.notification_type == NotificationType.ORDER_SHIPPED else None,
            actual_delivery_date=datetime.utcnow() if request.notification_type == NotificationType.ORDER_DELIVERED else None
        )

        # Save mock order to database (temporary)
        order_dict = mock_order.model_dump(by_alias=True, exclude={"id"})
        result = await db.orders.insert_one(order_dict)
        mock_order.id = result.inserted_id

        # Initialize notification service
        notification_service = NotificationService(db, settings.email_from)

        # Send notification
        notification_id = await notification_service.send_order_notification(
            order=mock_order,
            notification_type=request.notification_type,
            background_tasks=background_tasks
        )

        if not notification_id:
            raise HTTPException(status_code=500, detail="Failed to send notification")

        return {
            "success": True,
            "message": "Test notification sent successfully",
            "notification_id": notification_id,
            "order_id": str(mock_order.id),
            "order_number": mock_order.order_number,
            "notification_type": request.notification_type,
            "language": request.language,
            "recipient_email": request.recipient_email
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")


@router.get("/logs", response_model=NotificationListResponse)
async def get_notification_logs(
    order_id: str = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get notification logs

    Args:
        order_id: Filter by order ID (optional)
        limit: Maximum number of logs to return (default: 50)
        skip: Number of logs to skip for pagination (default: 0)
    """
    try:
        notification_service = NotificationService(db, settings.email_from)
        logs = await notification_service.get_notification_logs(
            order_id=order_id,
            limit=limit,
            skip=skip
        )

        # Get total count
        query = {}
        if order_id:
            query["order_id"] = ObjectId(order_id)
        total = await db.notification_logs.count_documents(query)

        return NotificationListResponse(
            notifications=[
                NotificationResponse(
                    id=str(log.id),
                    notification_type=log.notification_type,
                    recipient_email=log.recipient_email,
                    recipient_name=log.recipient_name,
                    language=log.language,
                    order_id=str(log.order_id),
                    order_number=log.order_number,
                    subject=log.subject,
                    status=log.status,
                    retry_count=log.retry_count,
                    created_at=log.created_at,
                    sent_at=log.sent_at,
                    failed_at=log.failed_at,
                    last_error=log.last_error
                )
                for log in logs
            ],
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notification logs: {str(e)}")


@router.get("/logs/{notification_id}", response_model=NotificationResponse)
async def get_notification_log(
    notification_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a specific notification log by ID
    """
    try:
        log_dict = await db.notification_logs.find_one({"_id": ObjectId(notification_id)})

        if not log_dict:
            raise HTTPException(status_code=404, detail="Notification log not found")

        from app.models.notification import NotificationLog
        log = NotificationLog(**log_dict)

        return NotificationResponse(
            id=str(log.id),
            notification_type=log.notification_type,
            recipient_email=log.recipient_email,
            recipient_name=log.recipient_name,
            language=log.language,
            order_id=str(log.order_id),
            order_number=log.order_number,
            subject=log.subject,
            status=log.status,
            retry_count=log.retry_count,
            created_at=log.created_at,
            sent_at=log.sent_at,
            failed_at=log.failed_at,
            last_error=log.last_error
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to fetch notification log: {str(e)}")
