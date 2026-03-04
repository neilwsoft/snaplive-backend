from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId

def validate_object_id(v: any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class StreamMetric(BaseModel):
    """
    Time-series metric for a stream destination.
    Used for generating reports and charts.
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    destination_id: PyObjectId = Field(..., description="Reference to StreamDestination")
    platform: str = Field(..., description="Platform name (douyin, taobao, etc)")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metrics
    latency_ms: float = Field(..., description="Latency in milliseconds")
    bitrate_kbps: float = Field(..., description="Bitrate in kbps")
    fps: Optional[float] = Field(None, description="Frames per second")
    dropped_frames: int = Field(default=0, description="Dropped frames count since last metric")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
