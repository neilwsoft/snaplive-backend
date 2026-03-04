"""Health check endpoints"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_database

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Health check endpoint with MongoDB connection status

    Returns:
        dict: Health status and database connection info
    """
    try:
        # Ping MongoDB to check connection
        await db.client.admin.command('ping')
        mongodb_status = "connected"
    except Exception as e:
        mongodb_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "service": "snaplive-backend",
        "database": {
            "mongodb": mongodb_status,
            "database_name": db.name
        }
    }
