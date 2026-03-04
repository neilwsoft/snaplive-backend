from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
from app.adapters.base_platform_adapter import BasePlatformAdapter


class XiaohongshuMockAdapter(BasePlatformAdapter):
    """
    Mock adapter for Xiaohongshu (小红书/Red) platform.
    Simulates API responses without making real API calls.
    """

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "xiaohongshu"

    async def test_connection(self) -> Dict[str, Any]:
        """Simulate connection test to Xiaohongshu"""
        if not self.credentials.get("app_id") or not self.credentials.get("app_secret"):
            return {
                "success": False,
                "message": "Invalid credentials: Missing app_id or app_secret",
                "details": None,
            }

        return {
            "success": True,
            "message": "Successfully connected to Xiaohongshu Merchant Platform",
            "details": {
                "api_version": "1.0",
                "rate_limit": 3000,
                "rate_remaining": 2876,
                "connected_at": datetime.utcnow().isoformat(),
            },
        }

    async def get_store_info(self, store_id: str) -> Dict[str, Any]:
        """Get mock store information"""
        return {
            "store_id": store_id,
            "store_name": f"小红书店铺 {store_id}",
            "store_url": f"https://www.xiaohongshu.com/store/{store_id}",
            "status": "active",
            "follower_count": random.randint(5000, 300000),
            "total_products": random.randint(30, 300),
            "monthly_sales": random.randint(3000, 30000),
            "rating": round(random.uniform(4.6, 5.0), 2),
            "verified": True,
        }

    async def fetch_orders(
        self,
        store_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Generate mock orders"""
        orders = []
        for i in range(min(page_size, 10)):
            order_num = f"XHS{store_id}{random.randint(100000, 999999)}"
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))

            orders.append({
                "order_id": order_num,
                "order_number": order_num,
                "buyer_name": f"小红薯{random.randint(1000, 9999)}",
                "buyer_email": f"xhsuser{random.randint(1000, 9999)}@xhs.com",
                "total": round(random.uniform(40, 800), 2),
                "currency": "CNY",
                "status": status or random.choice(["pending", "paid", "shipped", "completed"]),
                "payment_status": "paid",
                "items": [
                    {
                        "product_id": f"XHSP{random.randint(10000, 99999)}",
                        "product_name": {
                            "ko": f"제품 {i+1}",
                            "zh": f"产品 {i+1}",
                        },
                        "quantity": random.randint(1, 4),
                        "unit_price": round(random.uniform(30, 400), 2),
                        "sku": f"XHSSKU{random.randint(1000, 9999)}",
                    }
                ],
                "shipping_address": {
                    "recipient_name": f"收货人{random.randint(100, 999)}",
                    "phone": f"187{random.randint(10000000, 99999999)}",
                    "address_line1": "上海市徐汇区",
                    "city": "上海市",
                    "province": "上海",
                    "postal_code": "200000",
                    "country": "CN",
                },
                "created_at": order_date.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            })

        return {
            "orders": orders,
            "total": 65,
            "page": page,
            "has_more": page < 7,
        }

    async def get_order_details(self, store_id: str, order_id: str) -> Dict[str, Any]:
        """Get mock order details"""
        return {
            "order_id": order_id,
            "order_number": order_id,
            "buyer_name": "小红薯8888",
            "buyer_email": "xhsuser8888@xhs.com",
            "total": 598.00,
            "currency": "CNY",
            "status": "shipped",
            "payment_status": "paid",
            "tracking_number": f"JD{random.randint(1000000000, 9999999999)}",
            "carrier": "京东物流",
            "items": [
                {
                    "product_id": "XHSP98765",
                    "product_name": {"ko": "테스트 제품", "zh": "测试产品"},
                    "quantity": 2,
                    "unit_price": 299.00,
                    "sku": "XHSSKU9876",
                }
            ],
        }

    async def fetch_inventory(
        self,
        store_id: str,
        product_ids: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Generate mock inventory data"""
        items = []
        for i in range(min(page_size, 20)):
            items.append({
                "product_id": f"XHSP{random.randint(10000, 99999)}",
                "sku": f"XHSSKU{random.randint(1000, 9999)}",
                "quantity": random.randint(0, 200),
                "reserved_quantity": random.randint(0, 20),
                "available_quantity": random.randint(0, 180),
                "warehouse": "上海仓库",
                "last_updated": datetime.utcnow().isoformat(),
            })

        return {
            "items": items,
            "total": 100,
            "page": page,
            "has_more": page < 5,
        }

    async def update_inventory(
        self,
        store_id: str,
        updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Simulate inventory update"""
        return {
            "success": True,
            "updated_count": len(updates),
            "errors": [],
            "details": [
                {
                    "product_id": update.get("product_id"),
                    "sku": update.get("sku"),
                    "old_quantity": random.randint(0, 100),
                    "new_quantity": update.get("quantity"),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                for update in updates
            ],
        }

    async def fetch_products(
        self,
        store_id: str,
        product_ids: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Generate mock products"""
        products = []
        for i in range(min(page_size, 15)):
            product_id = f"XHSP{random.randint(10000, 99999)}"
            products.append({
                "product_id": product_id,
                "name": {
                    "ko": f"상품 {i+1}",
                    "zh": f"商品 {i+1}",
                },
                "description": {
                    "ko": f"상품 설명 {i+1}",
                    "zh": f"商品描述 {i+1}",
                },
                "price": round(random.uniform(50, 1000), 2),
                "currency": "CNY",
                "sku": f"XHSSKU{random.randint(1000, 9999)}",
                "stock": random.randint(0, 200),
                "images": [
                    f"https://ci.xiaohongshu.com/mock/{product_id}_1.jpg",
                    f"https://ci.xiaohongshu.com/mock/{product_id}_2.jpg",
                ],
                "status": random.choice(["active", "inactive", "out_of_stock"]),
                "category": random.choice(["美妆", "时尚", "美食", "家居"]),
                "likes": random.randint(500, 10000),
                "favorites": random.randint(100, 5000),
                "notes_count": random.randint(10, 500),  # Number of related notes/posts
                "created_at": (datetime.utcnow() - timedelta(days=random.randint(0, 365))).isoformat(),
            })

        return {
            "products": products,
            "total": 90,
            "page": page,
            "has_more": page < 6,
        }

    async def create_product(
        self,
        store_id: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate product creation"""
        new_product_id = f"XHSP{random.randint(10000, 99999)}"
        return {
            "success": True,
            "product_id": new_product_id,
            "details": {
                **product_data,
                "product_id": new_product_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
            },
        }

    async def update_product(
        self,
        store_id: str,
        product_id: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate product update"""
        return {
            "success": True,
            "details": {
                **product_data,
                "product_id": product_id,
                "updated_at": datetime.utcnow().isoformat(),
            },
        }

    async def get_stream_analytics(
        self,
        store_id: str,
        stream_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate mock stream analytics"""
        streams = []
        for i in range(6):
            stream_date = datetime.utcnow() - timedelta(days=i)
            streams.append({
                "stream_id": f"XHSLIVE{random.randint(100000, 999999)}",
                "title": f"直播分享{i+1}",
                "started_at": stream_date.isoformat(),
                "ended_at": (stream_date + timedelta(hours=random.randint(1, 3))).isoformat(),
                "duration_minutes": random.randint(60, 180),
                "total_viewers": random.randint(2000, 30000),
                "peak_viewers": random.randint(1000, 10000),
                "unique_viewers": random.randint(1500, 25000),
                "average_watch_time_minutes": round(random.uniform(10, 50), 1),
                "engagement_rate": round(random.uniform(20, 65), 1),
                "total_likes": random.randint(1000, 15000),
                "total_comments": random.randint(300, 3000),
                "total_shares": random.randint(50, 800),
                "total_favorites": random.randint(100, 2000),
            })

        return {
            "streams": streams,
            "metrics": {
                "total_streams": len(streams),
                "total_viewers": sum(s["total_viewers"] for s in streams),
                "average_viewers": round(sum(s["total_viewers"] for s in streams) / len(streams)),
                "total_watch_time_hours": round(sum(s["duration_minutes"] for s in streams) / 60, 1),
            },
        }

    async def get_stream_products(
        self,
        store_id: str,
        stream_id: str,
    ) -> Dict[str, Any]:
        """Generate mock stream products data"""
        products = []
        for i in range(8):
            product_id = f"XHSP{random.randint(10000, 99999)}"
            products.append({
                "product_id": product_id,
                "name": {"ko": f"상품 {i+1}", "zh": f"商品 {i+1}"},
                "clicks": random.randint(80, 800),
                "views": random.randint(300, 3000),
                "purchases": random.randint(8, 80),
                "revenue": round(random.uniform(400, 8000), 2),
                "conversion_rate": round(random.uniform(10, 30), 1),
                "likes": random.randint(50, 500),
                "favorites": random.randint(20, 200),
            })

        return {
            "products": products,
            "clicks": sum(p["clicks"] for p in products),
            "conversions": sum(p["purchases"] for p in products),
        }

    async def get_rtmp_config(self, store_id: str) -> Dict[str, Any]:
        """Generate mock RTMP configuration"""
        stream_key = f"live_xhs_{store_id}_{random.randint(100000, 999999)}"
        return {
            "rtmp_url": "rtmp://push.xhslive.com/live",
            "stream_key": stream_key,
            "backup_url": "rtmp://backup.xhslive.com/live",
            "backup_stream_key": f"backup_{stream_key}",
            "max_bitrate_kbps": 5000,
            "recommended_bitrate_kbps": 3500,
            "max_resolution": "1920x1080",
            "supported_codecs": ["h264"],
        }

    async def start_live_stream(
        self,
        store_id: str,
        stream_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate starting a live stream"""
        stream_id = f"XHSLIVE{random.randint(100000, 999999)}"
        return {
            "success": True,
            "stream_id": stream_id,
            "rtmp_url": "rtmp://push.xhslive.com/live",
            "stream_key": f"live_xhs_{store_id}_{stream_id}",
            "stream_url": f"https://www.xiaohongshu.com/live/{stream_id}",
            "started_at": datetime.utcnow().isoformat(),
        }

    async def end_live_stream(
        self,
        store_id: str,
        stream_id: str,
    ) -> Dict[str, Any]:
        """Simulate ending a live stream"""
        return {
            "success": True,
            "final_metrics": {
                "stream_id": stream_id,
                "duration_minutes": random.randint(90, 180),
                "total_viewers": random.randint(2000, 30000),
                "peak_viewers": random.randint(1000, 10000),
                "total_revenue": round(random.uniform(3000, 60000), 2),
                "total_orders": random.randint(30, 300),
                "engagement_rate": round(random.uniform(20, 65), 1),
                "total_favorites": random.randint(100, 2000),
                "ended_at": datetime.utcnow().isoformat(),
            },
        }
