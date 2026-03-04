from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
from app.adapters.base_platform_adapter import BasePlatformAdapter


class DouyinMockAdapter(BasePlatformAdapter):
    """
    Mock adapter for Douyin (抖音) platform.
    Simulates API responses without making real API calls.
    """

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "douyin"

    async def test_connection(self) -> Dict[str, Any]:
        """Simulate connection test to Douyin"""
        if not self.credentials.get("client_key") or not self.credentials.get("client_secret"):
            return {
                "success": False,
                "message": "Invalid credentials: Missing client_key or client_secret",
                "details": None,
            }

        return {
            "success": True,
            "message": "Successfully connected to Douyin Open Platform",
            "details": {
                "api_version": "v1",
                "rate_limit": 5000,
                "rate_remaining": 4876,
                "connected_at": datetime.utcnow().isoformat(),
            },
        }

    async def get_store_info(self, store_id: str) -> Dict[str, Any]:
        """Get mock store information"""
        return {
            "store_id": store_id,
            "store_name": f"抖音小店 {store_id}",
            "store_url": f"https://haohuo.jinritemai.com/views/shop/index?id={store_id}",
            "status": "active",
            "follower_count": random.randint(10000, 500000),
            "total_products": random.randint(50, 500),
            "monthly_sales": random.randint(10000, 100000),
            "rating": round(random.uniform(4.7, 5.0), 2),
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
            order_num = f"DY{store_id}{random.randint(100000, 999999)}"
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))

            orders.append({
                "order_id": order_num,
                "order_number": order_num,
                "buyer_name": f"抖音用户{random.randint(1000, 9999)}",
                "buyer_email": f"dyuser{random.randint(1000, 9999)}@douyin.com",
                "total": round(random.uniform(30, 600), 2),
                "currency": "CNY",
                "status": status or random.choice(["pending", "paid", "shipped", "completed"]),
                "payment_status": "paid",
                "items": [
                    {
                        "product_id": f"DYP{random.randint(10000, 99999)}",
                        "product_name": {
                            "ko": f"제품 {i+1}",
                            "zh": f"产品 {i+1}",
                        },
                        "quantity": random.randint(1, 3),
                        "unit_price": round(random.uniform(20, 300), 2),
                        "sku": f"DYSKU{random.randint(1000, 9999)}",
                    }
                ],
                "shipping_address": {
                    "recipient_name": f"收货人{random.randint(100, 999)}",
                    "phone": f"156{random.randint(10000000, 99999999)}",
                    "address_line1": "北京市朝阳区",
                    "city": "北京市",
                    "province": "北京",
                    "postal_code": "100000",
                    "country": "CN",
                },
                "created_at": order_date.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            })

        return {
            "orders": orders,
            "total": 85,
            "page": page,
            "has_more": page < 9,
        }

    async def get_order_details(self, store_id: str, order_id: str) -> Dict[str, Any]:
        """Get mock order details"""
        return {
            "order_id": order_id,
            "order_number": order_id,
            "buyer_name": "抖音用户5678",
            "buyer_email": "dyuser5678@douyin.com",
            "total": 388.88,
            "currency": "CNY",
            "status": "shipped",
            "payment_status": "paid",
            "tracking_number": f"SF{random.randint(1000000000, 9999999999)}",
            "carrier": "顺丰速运",
            "items": [
                {
                    "product_id": "DYP54321",
                    "product_name": {"ko": "테스트 제품", "zh": "测试产品"},
                    "quantity": 1,
                    "unit_price": 388.88,
                    "sku": "DYSKU5678",
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
                "product_id": f"DYP{random.randint(10000, 99999)}",
                "sku": f"DYSKU{random.randint(1000, 9999)}",
                "quantity": random.randint(0, 300),
                "reserved_quantity": random.randint(0, 30),
                "available_quantity": random.randint(0, 270),
                "warehouse": "北京仓库",
                "last_updated": datetime.utcnow().isoformat(),
            })

        return {
            "items": items,
            "total": 150,
            "page": page,
            "has_more": page < 8,
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
            product_id = f"DYP{random.randint(10000, 99999)}"
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
                "price": round(random.uniform(20, 800), 2),
                "currency": "CNY",
                "sku": f"DYSKU{random.randint(1000, 9999)}",
                "stock": random.randint(0, 300),
                "images": [
                    f"https://p3-e.douyinpic.com/mock/{product_id}_1.jpg",
                    f"https://p3-e.douyinpic.com/mock/{product_id}_2.jpg",
                ],
                "status": random.choice(["active", "inactive", "out_of_stock"]),
                "category": random.choice(["美妆", "服饰", "数码", "食品"]),
                "views": random.randint(1000, 50000),
                "likes": random.randint(100, 10000),
                "created_at": (datetime.utcnow() - timedelta(days=random.randint(0, 365))).isoformat(),
            })

        return {
            "products": products,
            "total": 120,
            "page": page,
            "has_more": page < 8,
        }

    async def create_product(
        self,
        store_id: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate product creation"""
        new_product_id = f"DYP{random.randint(10000, 99999)}"
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
        for i in range(7):
            stream_date = datetime.utcnow() - timedelta(days=i)
            streams.append({
                "stream_id": f"DYLIVE{random.randint(100000, 999999)}",
                "title": f"直播带货{i+1}",
                "started_at": stream_date.isoformat(),
                "ended_at": (stream_date + timedelta(hours=random.randint(1, 4))).isoformat(),
                "duration_minutes": random.randint(60, 240),
                "total_viewers": random.randint(5000, 50000),
                "peak_viewers": random.randint(2000, 20000),
                "unique_viewers": random.randint(4000, 40000),
                "average_watch_time_minutes": round(random.uniform(8, 60), 1),
                "engagement_rate": round(random.uniform(15, 70), 1),
                "total_likes": random.randint(2000, 20000),
                "total_comments": random.randint(500, 5000),
                "total_shares": random.randint(100, 1000),
                "total_gifts": random.randint(50, 500),
                "gift_revenue_cny": round(random.uniform(500, 5000), 2),
            })

        return {
            "streams": streams,
            "metrics": {
                "total_streams": len(streams),
                "total_viewers": sum(s["total_viewers"] for s in streams),
                "average_viewers": round(sum(s["total_viewers"] for s in streams) / len(streams)),
                "total_watch_time_hours": round(sum(s["duration_minutes"] for s in streams) / 60, 1),
                "total_gift_revenue": sum(s["gift_revenue_cny"] for s in streams),
            },
        }

    async def get_stream_products(
        self,
        store_id: str,
        stream_id: str,
    ) -> Dict[str, Any]:
        """Generate mock stream products data"""
        products = []
        for i in range(12):
            product_id = f"DYP{random.randint(10000, 99999)}"
            products.append({
                "product_id": product_id,
                "name": {"ko": f"상품 {i+1}", "zh": f"商品 {i+1}"},
                "clicks": random.randint(100, 1000),
                "views": random.randint(500, 5000),
                "purchases": random.randint(10, 100),
                "revenue": round(random.uniform(500, 10000), 2),
                "conversion_rate": round(random.uniform(8, 25), 1),
                "comments": random.randint(20, 200),
            })

        return {
            "products": products,
            "clicks": sum(p["clicks"] for p in products),
            "conversions": sum(p["purchases"] for p in products),
        }

    async def get_rtmp_config(self, store_id: str) -> Dict[str, Any]:
        """Generate mock RTMP configuration"""
        stream_key = f"live_dy_{store_id}_{random.randint(100000, 999999)}"
        return {
            "rtmp_url": "rtmp://push.live.douyin.com/live",
            "stream_key": stream_key,
            "backup_url": "rtmp://backup.live.douyin.com/live",
            "backup_stream_key": f"backup_{stream_key}",
            "max_bitrate_kbps": 8000,
            "recommended_bitrate_kbps": 5000,
            "max_resolution": "1920x1080",
            "supported_codecs": ["h264"],
        }

    async def start_live_stream(
        self,
        store_id: str,
        stream_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate starting a live stream"""
        stream_id = f"DYLIVE{random.randint(100000, 999999)}"
        return {
            "success": True,
            "stream_id": stream_id,
            "rtmp_url": "rtmp://push.live.douyin.com/live",
            "stream_key": f"live_dy_{store_id}_{stream_id}",
            "stream_url": f"https://live.douyin.com/{stream_id}",
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
                "duration_minutes": random.randint(90, 240),
                "total_viewers": random.randint(5000, 50000),
                "peak_viewers": random.randint(2000, 20000),
                "total_revenue": round(random.uniform(5000, 100000), 2),
                "total_orders": random.randint(50, 500),
                "engagement_rate": round(random.uniform(15, 70), 1),
                "gift_revenue": round(random.uniform(500, 5000), 2),
                "ended_at": datetime.utcnow().isoformat(),
            },
        }
