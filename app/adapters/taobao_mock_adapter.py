from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
from app.adapters.base_platform_adapter import BasePlatformAdapter


class TaobaoMockAdapter(BasePlatformAdapter):
    """
    Mock adapter for Taobao platform.
    Simulates API responses without making real API calls.
    """

    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.platform_name = "taobao"

    async def test_connection(self) -> Dict[str, Any]:
        """Simulate connection test to Taobao"""
        # Simulate validation
        if not self.credentials.get("app_key") or not self.credentials.get("app_secret"):
            return {
                "success": False,
                "message": "Invalid credentials: Missing app_key or app_secret",
                "details": None,
            }

        return {
            "success": True,
            "message": "Successfully connected to Taobao Live",
            "details": {
                "api_version": "2.0",
                "rate_limit": 10000,
                "rate_remaining": 9876,
                "connected_at": datetime.utcnow().isoformat(),
            },
        }

    async def get_store_info(self, store_id: str) -> Dict[str, Any]:
        """Get mock store information"""
        return {
            "store_id": store_id,
            "store_name": f"Taobao Store {store_id}",
            "store_url": f"https://shop{store_id}.taobao.com",
            "status": "active",
            "seller_level": "gold",
            "total_products": random.randint(100, 1000),
            "monthly_sales": random.randint(5000, 50000),
            "rating": round(random.uniform(4.5, 5.0), 2),
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
        # Generate 10 mock orders
        orders = []
        for i in range(min(page_size, 10)):
            order_num = f"TB{store_id}{random.randint(100000, 999999)}"
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))

            orders.append({
                "order_id": order_num,
                "order_number": order_num,
                "buyer_name": f"买家{random.randint(1000, 9999)}",
                "buyer_email": f"buyer{random.randint(1000, 9999)}@example.com",
                "total": round(random.uniform(50, 500), 2),
                "currency": "CNY",
                "status": status or random.choice(["pending", "paid", "shipped", "completed"]),
                "payment_status": "paid",
                "items": [
                    {
                        "product_id": f"P{random.randint(10000, 99999)}",
                        "product_name": {
                            "ko": f"제품 {i+1}",
                            "zh": f"产品 {i+1}",
                        },
                        "quantity": random.randint(1, 5),
                        "unit_price": round(random.uniform(10, 200), 2),
                        "sku": f"SKU{random.randint(1000, 9999)}",
                    }
                ],
                "shipping_address": {
                    "recipient_name": f"收货人{random.randint(100, 999)}",
                    "phone": f"138{random.randint(10000000, 99999999)}",
                    "address_line1": "浙江省杭州市滨江区",
                    "city": "杭州市",
                    "province": "浙江省",
                    "postal_code": "310000",
                    "country": "CN",
                },
                "created_at": order_date.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            })

        return {
            "orders": orders,
            "total": 100,  # Mock total
            "page": page,
            "has_more": page < 10,
        }

    async def get_order_details(self, store_id: str, order_id: str) -> Dict[str, Any]:
        """Get mock order details"""
        return {
            "order_id": order_id,
            "order_number": order_id,
            "buyer_name": "买家1234",
            "buyer_email": "buyer1234@example.com",
            "total": 299.99,
            "currency": "CNY",
            "status": "shipped",
            "payment_status": "paid",
            "tracking_number": f"YT{random.randint(1000000000, 9999999999)}",
            "carrier": "中通快递",
            "items": [
                {
                    "product_id": "P12345",
                    "product_name": {"ko": "테스트 제품", "zh": "测试产品"},
                    "quantity": 2,
                    "unit_price": 149.99,
                    "sku": "SKU1234",
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
                "product_id": f"P{random.randint(10000, 99999)}",
                "sku": f"SKU{random.randint(1000, 9999)}",
                "quantity": random.randint(0, 500),
                "reserved_quantity": random.randint(0, 50),
                "available_quantity": random.randint(0, 450),
                "warehouse": "杭州仓库",
                "last_updated": datetime.utcnow().isoformat(),
            })

        return {
            "items": items,
            "total": 200,  # Mock total
            "page": page,
            "has_more": page < 10,
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
            product_id = f"P{random.randint(10000, 99999)}"
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
                "price": round(random.uniform(10, 500), 2),
                "currency": "CNY",
                "sku": f"SKU{random.randint(1000, 9999)}",
                "stock": random.randint(0, 500),
                "images": [
                    f"https://img.alicdn.com/mock/{product_id}_1.jpg",
                    f"https://img.alicdn.com/mock/{product_id}_2.jpg",
                ],
                "status": random.choice(["active", "inactive", "out_of_stock"]),
                "category": random.choice(["电子产品", "服装", "食品", "家居"]),
                "created_at": (datetime.utcnow() - timedelta(days=random.randint(0, 365))).isoformat(),
            })

        return {
            "products": products,
            "total": 150,  # Mock total
            "page": page,
            "has_more": page < 10,
        }

    async def create_product(
        self,
        store_id: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate product creation"""
        new_product_id = f"P{random.randint(10000, 99999)}"
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
        for i in range(5):
            stream_date = datetime.utcnow() - timedelta(days=i)
            streams.append({
                "stream_id": f"LS{random.randint(100000, 999999)}",
                "title": f"直播{i+1}",
                "started_at": stream_date.isoformat(),
                "ended_at": (stream_date + timedelta(hours=2)).isoformat(),
                "duration_minutes": random.randint(60, 180),
                "total_viewers": random.randint(1000, 10000),
                "peak_viewers": random.randint(500, 5000),
                "unique_viewers": random.randint(800, 8000),
                "average_watch_time_minutes": round(random.uniform(5, 45), 1),
                "engagement_rate": round(random.uniform(10, 60), 1),
                "total_likes": random.randint(500, 5000),
                "total_comments": random.randint(100, 1000),
                "total_shares": random.randint(50, 500),
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
        for i in range(10):
            product_id = f"P{random.randint(10000, 99999)}"
            products.append({
                "product_id": product_id,
                "name": {"ko": f"상품 {i+1}", "zh": f"商品 {i+1}"},
                "clicks": random.randint(50, 500),
                "views": random.randint(100, 1000),
                "purchases": random.randint(5, 50),
                "revenue": round(random.uniform(100, 5000), 2),
                "conversion_rate": round(random.uniform(5, 20), 1),
            })

        return {
            "products": products,
            "clicks": sum(p["clicks"] for p in products),
            "conversions": sum(p["purchases"] for p in products),
        }

    async def get_rtmp_config(self, store_id: str) -> Dict[str, Any]:
        """Generate mock RTMP configuration"""
        stream_key = f"live_{store_id}_{random.randint(100000, 999999)}"
        return {
            "rtmp_url": "rtmp://live.taobao.com/live",
            "stream_key": stream_key,
            "backup_url": "rtmp://backup.taobao.com/live",
            "backup_stream_key": f"backup_{stream_key}",
            "max_bitrate_kbps": 6000,
            "recommended_bitrate_kbps": 4000,
            "max_resolution": "1920x1080",
            "supported_codecs": ["h264", "h265"],
        }

    async def start_live_stream(
        self,
        store_id: str,
        stream_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Simulate starting a live stream"""
        stream_id = f"LS{random.randint(100000, 999999)}"
        return {
            "success": True,
            "stream_id": stream_id,
            "rtmp_url": "rtmp://live.taobao.com/live",
            "stream_key": f"live_{store_id}_{stream_id}",
            "stream_url": f"https://live.taobao.com/stream/{stream_id}",
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
                "duration_minutes": random.randint(60, 180),
                "total_viewers": random.randint(1000, 10000),
                "peak_viewers": random.randint(500, 5000),
                "total_revenue": round(random.uniform(1000, 50000), 2),
                "total_orders": random.randint(10, 200),
                "engagement_rate": round(random.uniform(10, 60), 1),
                "ended_at": datetime.utcnow().isoformat(),
            },
        }
