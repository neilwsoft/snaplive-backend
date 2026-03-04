from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.auth import UserResponse, UserUpdate, PasswordChange
from app.utils.security import get_current_active_user
from app.services.auth import AuthService

router = APIRouter()


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: Optional[str] = Query(None, description="Search query for name or email"),
    limit: int = Query(20, le=50, description="Maximum number of results"),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Search registered users by name or email.

    - **q**: Search query string (optional, returns all active users if empty)
    - **limit**: Maximum number of results (default 20, max 50)

    Returns list of active users matching the search criteria.
    Requires authentication via Bearer token.
    """
    auth_service = AuthService(db)
    return await auth_service.search_users(query=q, limit=limit)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Get current user profile

    Requires authentication via Bearer token
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update current user profile

    - **full_name**: New full name (optional)
    - **email**: New email address (optional)

    Requires authentication via Bearer token
    """
    auth_service = AuthService(db)
    return await auth_service.update_user(current_user.email, user_data)


@router.put("/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Change current user's password

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, must contain uppercase, lowercase, digit)

    Requires authentication via Bearer token
    """
    auth_service = AuthService(db)
    return await auth_service.change_password(current_user.email, password_data)
