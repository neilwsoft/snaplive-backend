"""Order Service

Business logic for order management including statistics calculation.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.order import Order, OrderStatus, PaymentStatus, Platform


class OrderService:
    """Service for order operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.orders_collection = db.orders

    async def get_order_stats(self) -> Dict:
        """
        Calculate comprehensive order statistics for dashboard

        Returns:
            Dict containing order statistics including counts by status, platform, and trends
        """

        # Get total count
        total_orders = await self.orders_collection.count_documents({})

        # Get counts by status
        status_counts = {}
        for status in OrderStatus:
            count = await self.orders_collection.count_documents({"status": status.value})
            status_counts[status.value] = count

        # Get counts by payment status
        payment_status_counts = {}
        for payment_status in PaymentStatus:
            count = await self.orders_collection.count_documents({"payment_status": payment_status.value})
            payment_status_counts[payment_status.value] = count

        # Get counts by platform
        platform_counts = {}
        for platform in Platform:
            count = await self.orders_collection.count_documents({"platform": platform.value})
            platform_counts[platform.value] = count

        # Calculate total revenue (only completed payments)
        revenue_pipeline = [
            {"$match": {"payment_status": PaymentStatus.COMPLETED.value}},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$total"}}}
        ]
        revenue_result = await self.orders_collection.aggregate(revenue_pipeline).to_list(length=1)
        total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0.0

        # Calculate average order value
        avg_order_value = total_revenue / status_counts.get(OrderStatus.DELIVERED.value, 1) if status_counts.get(OrderStatus.DELIVERED.value, 0) > 0 else 0.0

        # Get orders over last 30 days for trends
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        orders_last_30_days = await self.orders_collection.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })

        # Get daily order counts for the last 30 days
        daily_orders_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        daily_orders_result = await self.orders_collection.aggregate(daily_orders_pipeline).to_list(length=30)
        daily_orders = [{"date": item["_id"], "count": item["count"]} for item in daily_orders_result]

        # Get daily orders by platform for the last 30 days
        daily_orders_by_platform_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at"
                            }
                        },
                        "platform": "$platform"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.date": 1}}
        ]
        daily_platform_result = await self.orders_collection.aggregate(daily_orders_by_platform_pipeline).to_list(length=None)
        daily_orders_by_platform = [
            {
                "date": item["_id"]["date"],
                "platform": item["_id"]["platform"],
                "count": item["count"]
            }
            for item in daily_platform_result
        ]

        return {
            "total_orders": total_orders,
            "status_counts": status_counts,
            "payment_status_counts": payment_status_counts,
            "platform_counts": platform_counts,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(avg_order_value, 2),
            "orders_last_30_days": orders_last_30_days,
            "daily_orders": daily_orders,
            "daily_orders_by_platform": daily_orders_by_platform,
            # Specific status counts for easy access
            "pending_orders": status_counts.get(OrderStatus.PENDING.value, 0),
            "confirmed_orders": status_counts.get(OrderStatus.READY.value, 0),  # ready = confirmed
            "processing_orders": status_counts.get(OrderStatus.SHOPPING.value, 0),  # shopping = processing
            "shipped_orders": status_counts.get(OrderStatus.SHIPPED.value, 0),
            "delivered_orders": status_counts.get(OrderStatus.DELIVERED.value, 0),
            "cancelled_orders": status_counts.get(OrderStatus.CANCELLED.value, 0),
        }

    async def get_orders(
        self,
        status: Optional[OrderStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        platform: Optional[Platform] = None,
        buyer_email: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Order], int]:
        """
        Get orders with filtering and pagination

        Args:
            status: Filter by order status
            payment_status: Filter by payment status
            platform: Filter by platform
            buyer_email: Filter by buyer email
            search: Search by order number or buyer name
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (orders list, total count)
        """
        query = {}

        if status:
            query["status"] = status.value
        if payment_status:
            query["payment_status"] = payment_status.value
        if platform:
            query["platform"] = platform.value
        if buyer_email:
            query["buyer_email"] = {"$regex": buyer_email, "$options": "i"}
        if search:
            query["$or"] = [
                {"order_number": {"$regex": search, "$options": "i"}},
                {"buyer_name": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total = await self.orders_collection.count_documents(query)

        # Get paginated results
        skip = (page - 1) * page_size
        cursor = self.orders_collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        orders_data = await cursor.to_list(length=page_size)

        # Convert to Order models
        orders = [Order(**order_data) for order_data in orders_data]

        return orders, total

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get single order by ID"""
        if not ObjectId.is_valid(order_id):
            return None

        order_data = await self.orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order_data:
            return None

        return Order(**order_data)

    async def create_order(self, order: Order) -> Order:
        """Create a new order"""
        order_dict = order.model_dump(by_alias=True, exclude={"id"})
        result = await self.orders_collection.insert_one(order_dict)
        order.id = result.inserted_id
        return order

    async def update_order(self, order_id: str, update_data: dict) -> Optional[Order]:
        """Update an existing order"""
        if not ObjectId.is_valid(order_id):
            return None

        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()

        result = await self.orders_collection.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            return None

        try:
            return Order(**result)
        except Exception as e:
            print(f"Error validating updated order: {e}")
            # Also log the result to see what data failed validation
            print(f"Invalid order data: {result}")
            raise e

    async def delete_order(self, order_id: str) -> bool:
        """Delete an order"""
        if not ObjectId.is_valid(order_id):
            return False

        result = await self.orders_collection.delete_one({"_id": ObjectId(order_id)})
        return result.deleted_count > 0

    async def get_monthly_revenue_stats(self, months: int = 5) -> Dict:
        """
        Get monthly revenue breakdown for the dashboard RevenueWidget.

        Args:
            months: Number of months to return (default 5)

        Returns:
            Dict containing monthly revenue data with comparison metrics
        """
        # Calculate date range - go back N months from the start of current month
        now = datetime.utcnow()
        # Start from the first day of the month, N months ago
        start_date = datetime(now.year, now.month, 1) - timedelta(days=months * 31)
        start_date = datetime(start_date.year, start_date.month, 1)

        # Aggregate revenue by month (only completed payments)
        pipeline = [
            {
                "$match": {
                    "payment_status": PaymentStatus.COMPLETED.value,
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"}
                    },
                    "revenue": {"$sum": "$total"},
                    "subtotal": {"$sum": "$subtotal"},
                    "order_count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]

        result = await self.orders_collection.aggregate(pipeline).to_list(length=months + 1)

        # Transform to response format
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_data = []

        for item in result[-months:]:  # Take last N months
            month_num = item["_id"]["month"]
            year = item["_id"]["year"]
            revenue = item["revenue"]
            # Estimate cost as 70% of subtotal (before fees/tax)
            cost = item["subtotal"] * 0.7 if item["subtotal"] else revenue * 0.7

            monthly_data.append({
                "month": f"{year}-{month_num:02d}",
                "month_label": month_names[month_num - 1],
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "order_count": item["order_count"]
            })

        # Calculate current vs previous month comparison
        current_revenue = monthly_data[-1]["revenue"] if monthly_data else 0
        previous_revenue = monthly_data[-2]["revenue"] if len(monthly_data) > 1 else 0

        if previous_revenue > 0:
            percentage_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
        else:
            percentage_change = 100.0 if current_revenue > 0 else 0.0

        return {
            "monthly_data": monthly_data,
            "current_month_revenue": current_revenue,
            "previous_month_revenue": previous_revenue,
            "percentage_change": round(percentage_change, 1),
            "total_revenue": sum(m["revenue"] for m in monthly_data)
        }
