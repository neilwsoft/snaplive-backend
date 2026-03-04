"""
Notification Service

This service handles email notifications for order lifecycle events.
It supports multiple languages (Korean and Chinese) and includes retry logic.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.notification import NotificationType, NotificationStatus, NotificationLog
from app.models.order import Order
from app.utils.email_sender import MockEmailSender

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending order notifications via email
    """

    def __init__(self, db: AsyncIOMotorDatabase, from_email: str = "noreply@snaplive.com"):
        """
        Initialize notification service

        Args:
            db: MongoDB database instance
            from_email: Sender email address
        """
        self.db = db
        self.email_sender = MockEmailSender(db, from_email)

        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Email subject templates
        self.subject_templates = {
            "ko": {
                NotificationType.ORDER_CONFIRMED: "주문이 확인되었습니다 - 주문번호 {order_number}",
                NotificationType.ORDER_SHIPPED: "상품이 배송되었습니다 - 주문번호 {order_number}",
                NotificationType.ORDER_DELIVERED: "상품이 배송완료되었습니다 - 주문번호 {order_number}",
                NotificationType.ORDER_CANCELLED: "주문이 취소되었습니다 - 주문번호 {order_number}",
            },
            "zh": {
                NotificationType.ORDER_CONFIRMED: "订单已确认 - 订单号 {order_number}",
                NotificationType.ORDER_SHIPPED: "商品已发货 - 订单号 {order_number}",
                NotificationType.ORDER_DELIVERED: "商品已送达 - 订单号 {order_number}",
                NotificationType.ORDER_CANCELLED: "订单已取消 - 订单号 {order_number}",
            }
        }

        # Template file mapping
        self.template_files = {
            NotificationType.ORDER_CONFIRMED: "order_confirmed",
            NotificationType.ORDER_SHIPPED: "order_shipped",
            NotificationType.ORDER_DELIVERED: "order_delivered",
            NotificationType.ORDER_CANCELLED: "order_cancelled",
        }

    async def send_order_notification(
        self,
        order: Order,
        notification_type: NotificationType,
        background_tasks=None
    ) -> Optional[str]:
        """
        Send an order notification email

        Args:
            order: Order object
            notification_type: Type of notification to send
            background_tasks: FastAPI BackgroundTasks for async sending

        Returns:
            Notification log ID if successful, None otherwise
        """
        try:
            # Create notification log
            notification_log = await self._create_notification_log(order, notification_type)

            if background_tasks:
                # Send asynchronously in background
                background_tasks.add_task(
                    self._send_notification_with_retry,
                    notification_log.id
                )
            else:
                # Send immediately
                await self._send_notification_with_retry(notification_log.id)

            return str(notification_log.id)

        except Exception as e:
            logger.error(f"Failed to initiate order notification: {str(e)}")
            return None

    async def _create_notification_log(
        self,
        order: Order,
        notification_type: NotificationType
    ) -> NotificationLog:
        """
        Create a notification log entry

        Args:
            order: Order object
            notification_type: Type of notification

        Returns:
            NotificationLog object
        """
        # Get subject
        language = order.buyer_language
        subject = self.subject_templates[language][notification_type].format(
            order_number=order.order_number
        )

        # Render email template
        html_body = await self._render_template(order, notification_type, language)

        # Create notification log
        notification_log = NotificationLog(
            notification_type=notification_type,
            recipient_email=order.buyer_email,
            recipient_name=order.buyer_name,
            language=language,
            order_id=order.id,
            order_number=order.order_number,
            subject=subject,
            body_html=html_body,
            status=NotificationStatus.PENDING
        )

        # Save to database
        result = await self.db.notification_logs.insert_one(
            notification_log.model_dump(by_alias=True, exclude={"id"})
        )
        notification_log.id = result.inserted_id

        return notification_log

    async def _render_template(
        self,
        order: Order,
        notification_type: NotificationType,
        language: str
    ) -> str:
        """
        Render email template

        Args:
            order: Order object
            notification_type: Type of notification
            language: Language code (ko or zh)

        Returns:
            Rendered HTML string
        """
        template_name = f"{self.template_files[notification_type]}_{language}.html"
        template = self.jinja_env.get_template(template_name)

        # Prepare template context
        context = {
            "order": order,
            "order_number": order.order_number,
            "buyer_name": order.buyer_name,
            "items": order.items,
            "total": order.total,
            "currency": order.currency,
            "shipping_address": order.shipping_address,
            "tracking_number": order.tracking_number,
            "carrier": order.carrier,
            "estimated_delivery_date": order.estimated_delivery_date,
            "actual_delivery_date": order.actual_delivery_date,
        }

        return template.render(**context)

    async def _send_notification_with_retry(
        self,
        notification_log_id: ObjectId,
        max_retries: int = 3
    ) -> bool:
        """
        Send notification with retry logic

        Args:
            notification_log_id: Notification log ID
            max_retries: Maximum number of retry attempts

        Returns:
            True if sent successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Get notification log
                notification_log_dict = await self.db.notification_logs.find_one(
                    {"_id": notification_log_id}
                )
                if not notification_log_dict:
                    logger.error(f"Notification log not found: {notification_log_id}")
                    return False

                notification_log = NotificationLog(**notification_log_dict)

                # Update status to retrying
                if attempt > 0:
                    await self.db.notification_logs.update_one(
                        {"_id": notification_log_id},
                        {
                            "$set": {
                                "status": NotificationStatus.RETRYING,
                                "retry_count": attempt
                            }
                        }
                    )

                # Send email
                success = await self.email_sender.send_email(
                    to_email=notification_log.recipient_email,
                    subject=notification_log.subject,
                    html_body=notification_log.body_html,
                    metadata={
                        "order_id": str(notification_log.order_id),
                        "order_number": notification_log.order_number,
                        "notification_type": notification_log.notification_type
                    }
                )

                if success:
                    # Update status to sent
                    await self.db.notification_logs.update_one(
                        {"_id": notification_log_id},
                        {
                            "$set": {
                                "status": NotificationStatus.SENT,
                                "sent_at": datetime.utcnow(),
                                "retry_count": attempt
                            }
                        }
                    )
                    logger.info(f"Notification sent successfully: {notification_log_id}")
                    return True
                else:
                    raise Exception("Email sender returned False")

            except Exception as e:
                logger.warning(
                    f"Notification send attempt {attempt + 1}/{max_retries} failed: {str(e)}"
                )

                if attempt < max_retries - 1:
                    # Wait before retrying (exponential backoff)
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries reached, mark as failed
                    await self.db.notification_logs.update_one(
                        {"_id": notification_log_id},
                        {
                            "$set": {
                                "status": NotificationStatus.FAILED,
                                "failed_at": datetime.utcnow(),
                                "last_error": str(e),
                                "retry_count": max_retries
                            }
                        }
                    )
                    logger.error(
                        f"Notification failed after {max_retries} attempts: {notification_log_id}"
                    )
                    return False

        return False

    async def get_notification_logs(
        self,
        order_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> list[NotificationLog]:
        """
        Get notification logs

        Args:
            order_id: Filter by order ID
            limit: Maximum number of logs to return
            skip: Number of logs to skip

        Returns:
            List of NotificationLog objects
        """
        query = {}
        if order_id:
            query["order_id"] = ObjectId(order_id)

        cursor = self.db.notification_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)

        return [NotificationLog(**log) for log in logs]
