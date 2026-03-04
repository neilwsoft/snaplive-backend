from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class BasePlatformAdapter(ABC):
    """
    Base interface for platform adapters.
    All platform-specific implementations should inherit from this class.
    """

    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize the adapter with credentials.

        Args:
            credentials: Dictionary containing platform-specific credentials
                        (api_key, api_secret, access_token, etc.)
        """
        self.credentials = credentials
        self.platform_name = "unknown"

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test if the connection to the platform is valid.

        Returns:
            Dict with keys: success (bool), message (str), details (dict)
        """
        pass

    @abstractmethod
    async def get_store_info(self, store_id: str) -> Dict[str, Any]:
        """
        Get store information from the platform.

        Args:
            store_id: Platform-specific store ID

        Returns:
            Dict with store information (name, url, status, etc.)
        """
        pass

    # ==================== Order Sync Methods ====================

    @abstractmethod
    async def fetch_orders(
        self,
        store_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Fetch orders from the platform.

        Args:
            store_id: Platform-specific store ID
            start_date: Filter orders from this date
            end_date: Filter orders until this date
            status: Filter by order status
            page: Page number
            page_size: Number of orders per page

        Returns:
            Dict with keys: orders (list), total (int), page (int), has_more (bool)
        """
        pass

    @abstractmethod
    async def get_order_details(self, store_id: str, order_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific order.

        Args:
            store_id: Platform-specific store ID
            order_id: Platform-specific order ID

        Returns:
            Dict with order details
        """
        pass

    # ==================== Inventory Sync Methods ====================

    @abstractmethod
    async def fetch_inventory(
        self,
        store_id: str,
        product_ids: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Fetch inventory/stock levels from the platform.

        Args:
            store_id: Platform-specific store ID
            product_ids: Optional list of specific product IDs to fetch
            page: Page number
            page_size: Number of items per page

        Returns:
            Dict with keys: items (list), total (int), page (int), has_more (bool)
        """
        pass

    @abstractmethod
    async def update_inventory(
        self,
        store_id: str,
        updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update inventory levels on the platform.

        Args:
            store_id: Platform-specific store ID
            updates: List of dicts with keys: product_id, sku, quantity

        Returns:
            Dict with keys: success (bool), updated_count (int), errors (list)
        """
        pass

    # ==================== Product Sync Methods ====================

    @abstractmethod
    async def fetch_products(
        self,
        store_id: str,
        product_ids: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Fetch product catalog from the platform.

        Args:
            store_id: Platform-specific store ID
            product_ids: Optional list of specific product IDs to fetch
            page: Page number
            page_size: Number of products per page

        Returns:
            Dict with keys: products (list), total (int), page (int), has_more (bool)
        """
        pass

    @abstractmethod
    async def create_product(
        self,
        store_id: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new product on the platform.

        Args:
            store_id: Platform-specific store ID
            product_data: Product information (name, price, description, images, etc.)

        Returns:
            Dict with keys: success (bool), product_id (str), details (dict)
        """
        pass

    @abstractmethod
    async def update_product(
        self,
        store_id: str,
        product_id: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update an existing product on the platform.

        Args:
            store_id: Platform-specific store ID
            product_id: Platform-specific product ID
            product_data: Updated product information

        Returns:
            Dict with keys: success (bool), details (dict)
        """
        pass

    # ==================== Live Stream Data Methods ====================

    @abstractmethod
    async def get_stream_analytics(
        self,
        store_id: str,
        stream_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Fetch live stream analytics from the platform.

        Args:
            store_id: Platform-specific store ID
            stream_id: Optional specific stream ID
            start_date: Filter from this date
            end_date: Filter until this date

        Returns:
            Dict with keys: streams (list), metrics (dict)
            Metrics include: total_viewers, peak_viewers, watch_time, engagement_rate, etc.
        """
        pass

    @abstractmethod
    async def get_stream_products(
        self,
        store_id: str,
        stream_id: str,
    ) -> Dict[str, Any]:
        """
        Get products shown during a specific live stream.

        Args:
            store_id: Platform-specific store ID
            stream_id: Platform-specific stream ID

        Returns:
            Dict with keys: products (list), clicks (dict), conversions (dict)
        """
        pass

    # ==================== RTMP Streaming Methods ====================

    @abstractmethod
    async def get_rtmp_config(self, store_id: str) -> Dict[str, Any]:
        """
        Get RTMP streaming configuration for the platform.

        Args:
            store_id: Platform-specific store ID

        Returns:
            Dict with keys: rtmp_url (str), stream_key (str), backup_url (str), etc.
        """
        pass

    @abstractmethod
    async def start_live_stream(
        self,
        store_id: str,
        stream_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Notify the platform that a live stream is starting.

        Args:
            store_id: Platform-specific store ID
            stream_config: Stream configuration (title, description, products, etc.)

        Returns:
            Dict with keys: success (bool), stream_id (str), rtmp_url (str), etc.
        """
        pass

    @abstractmethod
    async def end_live_stream(
        self,
        store_id: str,
        stream_id: str,
    ) -> Dict[str, Any]:
        """
        Notify the platform that a live stream has ended.

        Args:
            store_id: Platform-specific store ID
            stream_id: Platform-specific stream ID

        Returns:
            Dict with keys: success (bool), final_metrics (dict)
        """
        pass

    # ==================== Helper Methods ====================

    def _handle_api_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle API errors and return standardized error response.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred

        Returns:
            Standardized error dict
        """
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }
