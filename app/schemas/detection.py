"""Object detection schemas for Grounding DINO inference"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x1: float = Field(..., description="Top-left x coordinate")
    y1: float = Field(..., description="Top-left y coordinate")
    x2: float = Field(..., description="Bottom-right x coordinate")
    y2: float = Field(..., description="Bottom-right y coordinate")


class Detection(BaseModel):
    """Single object detection result"""
    class_id: int = Field(..., description="Detected class ID")
    class_name: str = Field(..., description="Detected class name")
    confidence: float = Field(..., description="Detection confidence score (0-1)")
    box: BoundingBox = Field(..., description="Bounding box coordinates")
    matched_product_id: Optional[str] = Field(None, description="Matched product ID from inventory")
    matched_product_name: Optional[str] = Field(None, description="Matched product display name")
    matched_product_price: Optional[float] = Field(None, description="Matched product price")
    matched_product_image: Optional[str] = Field(None, description="Matched product image URL")


class DetectFrameRequest(BaseModel):
    """Request to detect objects in a video frame using Grounding DINO"""
    image_data: str = Field(..., description="Base64 encoded image data")
    room_name: str = Field(..., description="Live room identifier")
    confidence_threshold: float = Field(default=0.4, ge=0.0, le=1.0, description="Minimum box confidence threshold")
    text_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum text matching threshold")
    text_prompts: Optional[List[str]] = Field(default=None, description="Text prompts for detection (uses defaults if None)")
    image_size: int = Field(default=480, description="Image size for inference (pixels)")


class DetectFrameResponse(BaseModel):
    """Response with detected objects"""
    detections: List[Detection] = Field(default_factory=list, description="List of detected objects")
    inference_time_ms: float = Field(..., description="Inference time in milliseconds")
    frame_width: int = Field(..., description="Original frame width")
    frame_height: int = Field(..., description="Original frame height")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")


class ToggleDetectionRequest(BaseModel):
    """Request to toggle detection on/off for a room"""
    room_name: str = Field(..., description="Live room identifier")
    enabled: bool = Field(..., description="Enable or disable detection")
    visible_to_viewers: bool = Field(default=True, description="Make detection visible to viewers")


class ToggleDetectionResponse(BaseModel):
    """Response for detection toggle"""
    room_name: str
    enabled: bool
    visible_to_viewers: bool
    message: str = Field(..., description="Status message")


class DetectionAnalytics(BaseModel):
    """Analytics data for detected products"""
    room_id: str = Field(..., description="Room identifier")
    session_id: str = Field(..., description="Streaming session ID")
    product_id: Optional[str] = Field(None, description="Matched product ID")
    detected_class: str = Field(..., description="Detected object class")
    confidence: float = Field(..., description="Detection confidence")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    duration_seconds: float = Field(default=0.0, description="How long object was visible")
    bounding_box: BoundingBox = Field(..., description="Bounding box coordinates")
