"""Simulcaster Schemas

Pydantic schemas for top simulcasters/leaderboard endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TopSimulcasterResponse(BaseModel):
    """Response model for a single top simulcaster"""
    seller_id: str = Field(..., description="Seller/user ID")
    rank: int = Field(..., description="Ranking position")
    name: str = Field(..., description="User's full name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    verified: bool = Field(default=False, description="Whether user is verified")
    platforms: List[str] = Field(default_factory=list, description="Platforms they stream on")
    total_views: int = Field(default=0, description="Total views across all sessions")
    total_likes: int = Field(default=0, description="Total likes/reactions")
    total_comments: int = Field(default=0, description="Total comments/messages")
    categories: List[str] = Field(default_factory=list, description="Categories they stream in")
    session_count: int = Field(default=0, description="Total number of sessions")


class TopSimulcastersListResponse(BaseModel):
    """Response model for top simulcasters list"""
    items: List[TopSimulcasterResponse]
    total: int = Field(..., description="Total number of simulcasters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
