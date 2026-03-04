"""Object detection service using Grounding DINO model"""

import logging
import io
import base64
import time
from typing import List, Optional, Dict, Any
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

from app.schemas.detection import Detection, BoundingBox
from app.config import settings

logger = logging.getLogger(__name__)


class DetectionService:
    """Service for Grounding DINO zero-shot object detection"""

    def __init__(self):
        """Initialize detection service"""
        self._model = None
        self._processor = None
        self._device = None
        self._model_loaded = False
        # Hardcoded prompts for initial implementation
        self._default_prompts = ["a bottle", "a mouse", "a headset", "a keyboard"]

    def _get_device(self) -> str:
        """
        Determine the best available device for inference

        Returns:
            Device string: 'cuda', 'mps', or 'cpu'
        """
        if self._device is not None:
            return self._device

        # Check for CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            self._device = "cuda"
            logger.info("Using CUDA device for inference")
        # Check for MPS (Mac Metal)
        elif torch.backends.mps.is_available():
            self._device = "mps"
            logger.info("Using MPS (Metal) device for inference")
        else:
            self._device = "cpu"
            logger.warning("No GPU available, using CPU for inference")

        return self._device

    def _load_model(self):
        """Load Grounding DINO model into memory (singleton pattern)"""
        if self._model_loaded:
            return

        try:
            logger.info("Loading Grounding DINO model...")
            start_time = time.time()

            # Load Grounding DINO model and processor
            model_id = "IDEA-Research/grounding-dino-tiny"

            logger.info(f"Downloading model from HuggingFace: {model_id}")
            self._processor = AutoProcessor.from_pretrained(model_id)
            self._model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id)

            # Move model to best available device
            device = self._get_device()
            self._model.to(device)

            load_time = time.time() - start_time
            logger.info(f"Grounding DINO model loaded on {device} in {load_time:.2f}s")
            self._model_loaded = True

        except Exception as e:
            logger.error(f"Failed to load Grounding DINO model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")

    def _decode_base64_image(self, image_data: str) -> Image.Image:
        """
        Decode base64 image string to PIL Image

        Args:
            image_data: Base64 encoded image (with or without data URI prefix)

        Returns:
            PIL Image object
        """
        try:
            # Remove data URI prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # Decode base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            return image

        except Exception as e:
            logger.error(f"Failed to decode image: {str(e)}")
            raise ValueError(f"Invalid image data: {str(e)}")

    async def detect_objects(
        self,
        image_data: str,
        confidence_threshold: float = 0.4,
        text_threshold: float = 0.3,
        text_prompts: Optional[List[str]] = None,
        image_size: int = 480,
        room_name: Optional[str] = None,
        product_matcher=None,
    ) -> tuple[List[Detection], float, tuple[int, int]]:
        """
        Perform zero-shot object detection using Grounding DINO

        Args:
            image_data: Base64 encoded image
            confidence_threshold: Minimum box confidence score (0-1), default 0.4
            text_threshold: Minimum text matching score (0-1), default 0.3
            text_prompts: Optional list of text prompts for detection
            image_size: Image size for inference (pixels), default 480
            room_name: Optional room identifier for context

        Returns:
            Tuple of (detections list, inference_time_ms, (width, height))
        """
        # Load model if not already loaded
        if not self._model_loaded:
            self._load_model()

        try:
            # Decode image
            image = self._decode_base64_image(image_data)
            original_size = image.size  # (width, height)

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Use provided prompts or defaults
            prompts = text_prompts or self._default_prompts

            # Format prompts for Grounding DINO (requires ". " separator and trailing ".")
            text_prompt = " . ".join(prompts) + " ."

            logger.info(f"Running detection with prompts: {text_prompt}")

            # Get device
            device = self._get_device()

            # Preprocess inputs
            inputs = self._processor(
                images=image,
                text=text_prompt,
                return_tensors="pt"
            ).to(device)

            # Run inference
            start_time = time.time()
            with torch.inference_mode():
                outputs = self._model(**inputs)

            # Post-process results
            results = self._processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                threshold=confidence_threshold,
                text_threshold=text_threshold,
                target_sizes=[(image.height, image.width)]
            )

            inference_time = (time.time() - start_time) * 1000  # Convert to ms

            # Extract detections
            detections = []
            if len(results) > 0:
                result = results[0]

                boxes = result["boxes"]
                scores = result["scores"]
                labels = result["labels"]

                for box, score, label in zip(boxes, scores, labels):
                    # Convert tensor to numpy for coordinates
                    box_coords = box.cpu().numpy()
                    x1, y1, x2, y2 = box_coords

                    # Try to match to product
                    match_result = await self._match_to_product(
                        class_name=label,
                        confidence=float(score),
                        room_name=room_name,
                        product_matcher=product_matcher,
                    )

                    detection = Detection(
                        class_id=0,  # Not used with Grounding DINO
                        class_name=label,
                        confidence=float(score),
                        box=BoundingBox(
                            x1=float(x1),
                            y1=float(y1),
                            x2=float(x2),
                            y2=float(y2)
                        ),
                        matched_product_id=match_result.product_id if match_result else None,
                        matched_product_name=match_result.product_name if match_result else None,
                        matched_product_price=match_result.unit_cost if match_result else None,
                        matched_product_image=match_result.image_url if match_result else None,
                    )
                    detections.append(detection)

            logger.info(
                f"Detected {len(detections)} objects in {inference_time:.2f}ms "
                f"(room: {room_name or 'unknown'}, prompts: {len(prompts)})"
            )

            return detections, inference_time, original_size

        except Exception as e:
            logger.error(f"Detection failed: {str(e)}")
            raise

    async def _match_to_product(
        self,
        class_name: str,
        confidence: float,
        room_name: Optional[str] = None,
        product_matcher=None,
    ):
        """
        Match detected object to a product using ProductMatcherService.

        Args:
            class_name: Detected object class (e.g., "bottle", "person")
            confidence: Detection confidence
            room_name: Room context for filtering products
            product_matcher: ProductMatcherService instance

        Returns:
            MatchResult if matched, None otherwise
        """
        if product_matcher is None:
            return None

        try:
            return await product_matcher.match(
                class_name=class_name,
                confidence=confidence,
                room_name=room_name,
            )
        except Exception as e:
            logger.error(f"Product matching failed for '{class_name}': {e}")
            return None

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model

        Returns:
            Model information dictionary
        """
        if not self._model_loaded:
            return {
                "loaded": False,
                "device": None
            }

        return {
            "loaded": True,
            "device": self._device,
            "model_type": "Grounding DINO Tiny",
            "model_id": "IDEA-Research/grounding-dino-tiny",
            "detection_type": "zero-shot",
            "default_prompts": self._default_prompts
        }

    def unload_model(self):
        """Unload model from memory"""
        if self._model is not None:
            self._model = None
            self._processor = None
            self._model_loaded = False
            logger.info("Grounding DINO model unloaded from memory")


# Singleton instance
detection_service = DetectionService()
