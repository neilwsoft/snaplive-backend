"""Object detection endpoints for Grounding DINO inference"""

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging

from app.database import get_database
from app.schemas.detection import (
    DetectFrameRequest,
    DetectFrameResponse,
    ToggleDetectionRequest,
    ToggleDetectionResponse
)
from app.services.detection_service import detection_service
from app.services.product_matcher_service import ProductMatcherService

router = APIRouter()
logger = logging.getLogger(__name__)

# Store detection state per room (in production, use Redis or database)
detection_state = {}


def get_matcher_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ProductMatcherService:
    """Dependency to get product matcher service"""
    return ProductMatcherService(db)


@router.post("/detect-frame", response_model=DetectFrameResponse)
async def detect_frame(
    request: DetectFrameRequest,
    matcher: ProductMatcherService = Depends(get_matcher_service),
):
    """
    Detect objects in a video frame using Grounding DINO zero-shot detection

    - **image_data**: Base64 encoded image (JPEG/PNG)
    - **room_name**: Live room identifier for context
    - **confidence_threshold**: Minimum box confidence (0-1, default 0.4)
    - **text_threshold**: Minimum text matching threshold (0-1, default 0.3)
    - **text_prompts**: Optional list of text prompts (uses defaults: bottle, mouse, headset, keyboard)
    - **image_size**: Image size for inference (default 480 for balanced performance)

    Returns detected objects with bounding boxes, class names, and matched product IDs.
    """
    try:
        # Check if detection is enabled for this room
        room_detection = detection_state.get(request.room_name, {"enabled": True})
        if not room_detection.get("enabled", True):
            return DetectFrameResponse(
                detections=[],
                inference_time_ms=0,
                frame_width=0,
                frame_height=0,
                timestamp=datetime.utcnow()
            )

        # Perform detection
        detections, inference_time, (width, height) = await detection_service.detect_objects(
            image_data=request.image_data,
            confidence_threshold=request.confidence_threshold,
            text_threshold=request.text_threshold,
            text_prompts=request.text_prompts,
            image_size=request.image_size,
            room_name=request.room_name,
            product_matcher=matcher,
        )

        logger.info(
            f"Frame detection: {len(detections)} objects, "
            f"{inference_time:.2f}ms inference time, "
            f"room: {request.room_name}"
        )

        return DetectFrameResponse(
            detections=detections,
            inference_time_ms=inference_time,
            frame_width=width,
            frame_height=height,
            timestamp=datetime.utcnow()
        )

    except ValueError as e:
        logger.error(f"Invalid image data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/toggle", response_model=ToggleDetectionResponse)
async def toggle_detection(request: ToggleDetectionRequest):
    """
    Toggle object detection on/off for a specific room

    - **room_name**: Live room identifier
    - **enabled**: Enable or disable detection
    - **visible_to_viewers**: Make detection visible to viewers (host control)

    This endpoint allows the host to control detection visibility.
    State is stored in memory (use Redis in production for scalability).
    """
    try:
        # Update detection state for room
        detection_state[request.room_name] = {
            "enabled": request.enabled,
            "visible_to_viewers": request.visible_to_viewers,
            "updated_at": datetime.utcnow()
        }

        message = (
            f"Detection {'enabled' if request.enabled else 'disabled'} for room {request.room_name}. "
            f"Visible to viewers: {request.visible_to_viewers}"
        )

        logger.info(message)

        return ToggleDetectionResponse(
            room_name=request.room_name,
            enabled=request.enabled,
            visible_to_viewers=request.visible_to_viewers,
            message=message
        )

    except Exception as e:
        logger.error(f"Failed to toggle detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle detection: {str(e)}")


@router.get("/state/{room_name}")
async def get_detection_state(room_name: str):
    """
    Get current detection state for a room

    Returns whether detection is enabled and visible to viewers.
    """
    try:
        state = detection_state.get(room_name, {
            "enabled": True,
            "visible_to_viewers": True,
            "updated_at": None
        })

        return {
            "room_name": room_name,
            **state
        }

    except Exception as e:
        logger.error(f"Failed to get detection state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


@router.get("/model-info")
async def get_model_info():
    """
    Get information about the loaded Grounding DINO model

    Returns model type, device, detection type, and default prompts.
    """
    try:
        info = detection_service.get_model_info()
        return info

    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")
