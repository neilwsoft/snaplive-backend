"""QR Code Generation Utility

Generates QR codes for shipment tracking.
"""

import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from typing import Literal


def generate_qr_code(
    data: str,
    size: int = 300,
    format: Literal["png", "svg"] = "png",
    error_correction: int = qrcode.constants.ERROR_CORRECT_M
) -> str:
    """
    Generate a QR code from the given data.

    Args:
        data: The data to encode in the QR code (e.g., tracking URL)
        size: Size of the QR code in pixels (default: 300)
        format: Output format - "png" or "svg" (default: "png")
        error_correction: Error correction level (default: M)

    Returns:
        Base64 encoded data URL string for the QR code

    Raises:
        ValueError: If format is not supported
    """
    # Calculate box_size and border based on desired pixel size
    # Default qrcode creates approximately 10 pixels per box
    box_size = max(1, size // 30)  # Approximate calculation
    border = 2

    if format == "png":
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Auto-adjust version
            error_correction=error_correction,
            box_size=box_size,
            border=border,
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Generate PIL image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 data URL
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    elif format == "svg":
        # Create QR code with SVG factory
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction,
            box_size=box_size,
            border=border,
            image_factory=qrcode.image.svg.SvgPathImage
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Generate SVG
        img = qr.make_image()

        # Convert to string
        buffer = BytesIO()
        img.save(buffer)
        svg_str = buffer.getvalue().decode('utf-8')

        return f"data:image/svg+xml;base64,{base64.b64encode(svg_str.encode()).decode()}"

    else:
        raise ValueError(f"Unsupported format: {format}. Use 'png' or 'svg'.")


def generate_tracking_qr(
    shipment_id: str,
    tracking_number: str,
    base_url: str = "https://snaplive.com/track",
    **kwargs
) -> str:
    """
    Generate a QR code for shipment tracking.

    Args:
        shipment_id: The shipment ID
        tracking_number: The tracking number
        base_url: Base URL for tracking page
        **kwargs: Additional arguments passed to generate_qr_code

    Returns:
        Base64 encoded data URL string for the QR code
    """
    # Create tracking URL
    tracking_url = f"{base_url}?shipment={shipment_id}&tracking={tracking_number}"

    return generate_qr_code(tracking_url, **kwargs)
