import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status

from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, UserUpdate, PasswordChange
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.config import get_settings

settings = get_settings()


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        user_dict = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": get_password_hash(user_data.password),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await self.db.users.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id

        return UserResponse(
            id=str(user_dict["_id"]),
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
        )

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return JWT tokens"""
        # Find user
        user = await self.db.users.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Check if user is active
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        # Create tokens
        token_data = {"sub": user["email"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data, remember_me=login_data.remember_me)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        payload = verify_token(refresh_token, token_type="refresh")

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Verify user still exists and is active
        user = await self.db.users.find_one({"email": email})
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        token_data = {"sub": email}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    async def request_password_reset(self, email: str) -> Dict[str, str]:
        """Request password reset token"""
        user = await self.db.users.find_one({"email": email})

        # Don't reveal if user exists or not for security
        if not user:
            return {"message": "If the email exists, a reset link has been sent"}

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=settings.password_reset_token_expire_hours)

        # Store reset token
        reset_data = {
            "email": email,
            "token": reset_token,
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.utcnow(),
        }

        await self.db.password_reset_tokens.insert_one(reset_data)

        # In a real application, you would send an email here
        # For now, we'll just return the token (remove this in production!)
        return {
            "message": "If the email exists, a reset link has been sent",
            "reset_token": reset_token  # Only for development/testing
        }

    async def reset_password(self, token: str, new_password: str) -> Dict[str, str]:
        """Reset password using token"""
        # Find reset token
        reset_token = await self.db.password_reset_tokens.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Update user password
        await self.db.users.update_one(
            {"email": reset_token["email"]},
            {
                "$set": {
                    "password_hash": get_password_hash(new_password),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Mark token as used
        await self.db.password_reset_tokens.update_one(
            {"_id": reset_token["_id"]},
            {"$set": {"used": True}}
        )

        return {"message": "Password reset successful"}

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email"""
        user = await self.db.users.find_one({"email": email})
        if not user:
            return None

        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        )

    async def search_users(
        self, query: Optional[str] = None, limit: int = 20
    ) -> list[UserResponse]:
        """Search users by name or email"""
        filter_query = {"is_active": True}

        if query and query.strip():
            # Case-insensitive search on full_name and email
            filter_query["$or"] = [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
            ]

        cursor = self.db.users.find(filter_query).limit(limit)
        users = await cursor.to_list(length=limit)

        return [
            UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                full_name=user["full_name"],
                is_active=user["is_active"],
                created_at=user["created_at"],
            )
            for user in users
        ]

    async def change_password(self, email: str, password_data: PasswordChange) -> Dict[str, str]:
        """Change password for authenticated user"""
        user = await self.db.users.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(password_data.current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        await self.db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "password_hash": get_password_hash(password_data.new_password),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {"message": "Password changed successfully"}

    async def update_user(self, email: str, user_data: UserUpdate) -> UserResponse:
        """Update user profile"""
        update_data = {}

        if user_data.full_name is not None:
            update_data["full_name"] = user_data.full_name

        if user_data.email is not None:
            # Check if new email already exists
            existing_user = await self.db.users.find_one({"email": user_data.email})
            if existing_user and existing_user["email"] != email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            update_data["email"] = user_data.email

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        update_data["updated_at"] = datetime.utcnow()

        # Update user
        result = await self.db.users.find_one_and_update(
            {"email": email},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=str(result["_id"]),
            email=result["email"],
            full_name=result["full_name"],
            is_active=result["is_active"],
            created_at=result["created_at"],
        )
