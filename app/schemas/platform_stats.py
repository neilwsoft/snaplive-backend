"""Platform Stats Schema

Response schema for aggregated platform statistics.
"""

from pydantic import BaseModel


class PlatformStatsResponse(BaseModel):
    live_sessions: int = 0
    active_viewers: int = 0
    total_users: int = 0
    marketplace_platforms: int = 0
