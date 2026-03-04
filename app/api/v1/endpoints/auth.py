from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Register a new user

    - **email**: Valid email address
    - **password**: Password (min 8 chars, must include uppercase, lowercase, and digit)
    - **full_name**: User's full name
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Login and get access token

    - **email**: User's email
    - **password**: User's password
    - **remember_me**: Extend token lifetime (default: false)
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(login_data)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(token_data.refresh_token)


@router.post("/forgot-password")
async def forgot_password(
    request_data: PasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Request password reset

    - **email**: User's email address

    Note: For security, this always returns success even if email doesn't exist
    """
    auth_service = AuthService(db)
    return await auth_service.request_password_reset(request_data.email)


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Reset password using token

    - **token**: Password reset token
    - **new_password**: New password (min 8 chars, must include uppercase, lowercase, and digit)
    """
    auth_service = AuthService(db)
    return await auth_service.reset_password(reset_data.token, reset_data.new_password)


@router.post("/logout")
async def logout():
    """
    Logout user

    Note: In a JWT-based system, logout is typically handled client-side
    by removing the tokens. This endpoint is here for completeness.
    """
    return {"message": "Successfully logged out"}
