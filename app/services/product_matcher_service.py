"""Product Matcher Service

Matches detected object class names to session products or inventory items
using a scored matching algorithm with caching.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Prefixes to strip from class names before matching
_ARTICLE_PREFIXES = ("a ", "an ", "the ")

# Cache TTL in seconds
_CACHE_TTL = 300  # 5 minutes


@dataclass
class MatchResult:
    """Result of a product match"""
    product_id: str
    product_name: str
    unit_cost: float
    image_url: Optional[str]
    match_score: float


@dataclass
class _CacheEntry:
    """Cached product data for a room"""
    products: List[Dict]
    timestamp: float


class ProductMatcherService:
    """Service for matching detected class names to products"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._cache: Dict[str, _CacheEntry] = {}

    def _strip_prefix(self, name: str) -> str:
        """Strip article prefixes and normalize a class name"""
        name = name.lower().strip()
        for prefix in _ARTICLE_PREFIXES:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name

    def _get_product_name_text(self, product_name) -> str:
        """Extract a flat text string from product_name (may be dict or str)"""
        if isinstance(product_name, dict):
            return " ".join(product_name.values()).lower()
        return str(product_name).lower()

    def _score_match(self, class_name: str, product: Dict) -> float:
        """Score how well a class name matches a product. Returns 0.0-1.0."""
        cn = self._strip_prefix(class_name)
        if not cn:
            return 0.0

        product_text = self._get_product_name_text(product.get("product_name", ""))
        category = (product.get("category") or "").lower()

        # Exact match on product name tokens
        if cn == product_text or cn in product_text.split():
            return 1.0

        # Substring containment (class_name in product name)
        if cn in product_text:
            return 0.8

        # Product name contains class_name as part of a compound word
        product_words = product_text.split()
        cn_words = cn.split()

        # Word-level token overlap
        if len(cn_words) > 0 and len(product_words) > 0:
            overlap = len(set(cn_words) & set(product_words))
            total = len(set(cn_words) | set(product_words))
            if overlap > 0 and total > 0:
                return 0.7 * (overlap / total)

        # Category match
        if category and (cn in category or category in cn):
            return 0.4

        return 0.0

    async def _get_session_products(self, room_name: str) -> List[Dict]:
        """Get products for a room from cache or DB"""
        now = time.time()

        # Check cache
        entry = self._cache.get(room_name)
        if entry and (now - entry.timestamp) < _CACHE_TTL:
            return entry.products

        # Query livestream_sessions collection
        products = []
        try:
            doc = await self.db.livestream_sessions.find_one(
                {"room_name": room_name},
                {"products": 1}
            )
            if doc and doc.get("products"):
                products = doc["products"]
                logger.info(
                    f"Loaded {len(products)} session products for room '{room_name}'"
                )
        except Exception as e:
            logger.error(f"Failed to query session products: {e}")

        # Update cache
        self._cache[room_name] = _CacheEntry(products=products, timestamp=now)
        return products

    async def _get_inventory_products(self, class_name: str) -> List[Dict]:
        """Fallback: search inventory collection for matching products"""
        try:
            cn = self._strip_prefix(class_name)
            cursor = self.db.inventory.find(
                {"product_name": {"$regex": cn, "$options": "i"}},
                {"product_id": 1, "product_name": 1, "unit_cost": 1,
                 "image_url": 1, "category": 1, "_id": 1}
            ).limit(10)
            return await cursor.to_list(length=10)
        except Exception as e:
            logger.error(f"Failed to query inventory: {e}")
            return []

    async def match(
        self,
        class_name: str,
        confidence: float,
        room_name: Optional[str] = None,
    ) -> Optional[MatchResult]:
        """
        Match a detected class name to a product.

        Tries session products first (threshold 0.3), then inventory (threshold 0.4).

        Args:
            class_name: Detected object class
            confidence: Detection confidence score
            room_name: Room name for session product lookup

        Returns:
            MatchResult if a match is found, None otherwise
        """
        best_match: Optional[MatchResult] = None
        best_score = 0.0

        # Try session products first
        if room_name:
            session_products = await self._get_session_products(room_name)
            for product in session_products:
                score = self._score_match(class_name, product)
                if score > best_score and score >= 0.3:
                    name_val = product.get("product_name", "")
                    if isinstance(name_val, dict):
                        display_name = name_val.get("en") or name_val.get("ko") or next(iter(name_val.values()), "")
                    else:
                        display_name = str(name_val)

                    best_match = MatchResult(
                        product_id=product.get("product_id", ""),
                        product_name=display_name,
                        unit_cost=product.get("unit_cost", 0.0),
                        image_url=product.get("image_url"),
                        match_score=score,
                    )
                    best_score = score

        # If no session match, try inventory
        if best_match is None:
            inventory_products = await self._get_inventory_products(class_name)
            for product in inventory_products:
                score = self._score_match(class_name, product)
                if score > best_score and score >= 0.4:
                    name_val = product.get("product_name", "")
                    if isinstance(name_val, dict):
                        display_name = name_val.get("en") or name_val.get("ko") or next(iter(name_val.values()), "")
                    else:
                        display_name = str(name_val)

                    best_match = MatchResult(
                        product_id=str(product.get("_id", product.get("product_id", ""))),
                        product_name=display_name,
                        unit_cost=product.get("unit_cost", 0.0),
                        image_url=product.get("image_url"),
                        match_score=score,
                    )
                    best_score = score

        if best_match:
            logger.debug(
                f"Matched '{class_name}' -> '{best_match.product_name}' "
                f"(score={best_match.match_score:.2f})"
            )

        return best_match
