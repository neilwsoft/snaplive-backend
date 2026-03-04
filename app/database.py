"""MongoDB database connection and management"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB on application startup"""
    logger.info("Connecting to MongoDB...")
    try:
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            minPoolSize=settings.mongodb_min_pool_size,
            maxPoolSize=settings.mongodb_max_pool_size,
        )
        db.db = db.client[settings.mongodb_db_name]

        # Verify connection
        await db.client.admin.command('ping')
        logger.info(f"Connected to MongoDB successfully - Database: {settings.mongodb_db_name}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown"""
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
    logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance"""
    return db.db
