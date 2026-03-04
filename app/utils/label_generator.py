"""Shipping Label Generation Utility

Generates PDF shipping labels for shipments.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from io import BytesIO
import base64
from typing import Dict, Optional
from datetime import datetime


def generate_shipping_label(
    shipment_number: str,
    tracking_number: Optional[str],
    carrier_name: str,
    origin: Dict,
    destination: Dict,
    package_details: Dict,
    qr_code_data_url: Optional[str] = None,
    page_size: str = "A4"
) -> str:
    """
    Generate a shipping label PDF.

    Args:
        shipment_number: The shipment number
        tracking_number: The carrier tracking number
        carrier_name: Name of the carrier
        origin: Origin address dict with keys: name, address_line1, city, postal_code, country, phone
        destination: Destination address dict (same structure as origin)
        package_details: Package dict with keys: weight, length, width, height
        qr_code_data_url: Optional QR code as data URL
        page_size: Page size - "A4" or "letter"

    Returns:
        Base64 encoded PDF data URL string
    """
    # Set up page size
    if page_size.upper() == "A4":
        page = A4
    else:
        page = letter

    # Create PDF in memory
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=page)
    width, height = page

    # Margins
    margin = 0.5 * inch
    y_position = height - margin

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, y_position, "SHIPPING LABEL")
    y_position -= 0.5 * inch

    # Draw horizontal line
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.line(margin, y_position, width - margin, y_position)
    y_position -= 0.4 * inch

    # Shipment Information Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y_position, "Shipment Information")
    y_position -= 0.3 * inch

    c.setFont("Helvetica", 11)
    c.drawString(margin, y_position, f"Shipment Number: {shipment_number}")
    y_position -= 0.25 * inch

    if tracking_number:
        c.drawString(margin, y_position, f"Tracking Number: {tracking_number}")
        y_position -= 0.25 * inch

    c.drawString(margin, y_position, f"Carrier: {carrier_name}")
    y_position -= 0.25 * inch

    c.drawString(margin, y_position, f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y_position -= 0.4 * inch

    # Draw horizontal line
    c.setLineWidth(1)
    c.line(margin, y_position, width - margin, y_position)
    y_position -= 0.4 * inch

    # Two column layout for addresses
    col1_x = margin
    col2_x = width / 2 + 0.25 * inch
    section_y = y_position

    # FROM Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(col1_x, section_y, "FROM:")
    section_y -= 0.3 * inch

    c.setFont("Helvetica", 10)
    c.drawString(col1_x, section_y, origin.get("name", ""))
    section_y -= 0.2 * inch
    c.drawString(col1_x, section_y, origin.get("address_line1", ""))
    section_y -= 0.2 * inch

    if origin.get("address_line2"):
        c.drawString(col1_x, section_y, origin.get("address_line2", ""))
        section_y -= 0.2 * inch

    city_postal = f"{origin.get('city', '')}, {origin.get('postal_code', '')}"
    c.drawString(col1_x, section_y, city_postal)
    section_y -= 0.2 * inch
    c.drawString(col1_x, section_y, origin.get("country", ""))
    section_y -= 0.2 * inch
    c.drawString(col1_x, section_y, f"Phone: {origin.get('phone', '')}")

    # TO Section
    section_y = y_position
    c.setFont("Helvetica-Bold", 14)
    c.drawString(col2_x, section_y, "TO:")
    section_y -= 0.3 * inch

    c.setFont("Helvetica-Bold", 12)  # Make recipient name bold
    c.drawString(col2_x, section_y, destination.get("name", ""))
    section_y -= 0.25 * inch

    c.setFont("Helvetica", 10)
    c.drawString(col2_x, section_y, destination.get("address_line1", ""))
    section_y -= 0.2 * inch

    if destination.get("address_line2"):
        c.drawString(col2_x, section_y, destination.get("address_line2", ""))
        section_y -= 0.2 * inch

    dest_city_postal = f"{destination.get('city', '')}, {destination.get('postal_code', '')}"
    c.drawString(col2_x, section_y, dest_city_postal)
    section_y -= 0.2 * inch
    c.drawString(col2_x, section_y, destination.get("country", ""))
    section_y -= 0.2 * inch
    c.drawString(col2_x, section_y, f"Phone: {destination.get('phone', '')}")

    y_position = section_y - 0.5 * inch

    # Draw horizontal line
    c.line(margin, y_position, width - margin, y_position)
    y_position -= 0.4 * inch

    # Package Details Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y_position, "Package Details")
    y_position -= 0.3 * inch

    c.setFont("Helvetica", 10)
    weight = package_details.get("weight", 0)
    c.drawString(margin, y_position, f"Weight: {weight} kg")
    y_position -= 0.2 * inch

    dimensions = []
    if package_details.get("length"):
        dimensions.append(f"L: {package_details['length']} cm")
    if package_details.get("width"):
        dimensions.append(f"W: {package_details['width']} cm")
    if package_details.get("height"):
        dimensions.append(f"H: {package_details['height']} cm")

    if dimensions:
        c.drawString(margin, y_position, f"Dimensions: {', '.join(dimensions)}")
        y_position -= 0.2 * inch

    if package_details.get("declared_value"):
        c.drawString(margin, y_position, f"Declared Value: ${package_details['declared_value']:.2f}")
        y_position -= 0.2 * inch

    # QR Code (if provided)
    if qr_code_data_url and qr_code_data_url.startswith("data:image"):
        y_position -= 0.3 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y_position, "Scan to Track:")

        # Note: In a real implementation, you would decode the base64 image
        # and draw it using c.drawImage(). For now, we'll just add a placeholder
        y_position -= 0.2 * inch
        c.setFont("Helvetica", 9)
        c.drawString(margin, y_position, "(QR Code would appear here)")

    # Footer
    y_position = margin + 0.5 * inch
    c.setFont("Helvetica", 8)
    c.drawString(margin, y_position, "This is a computer-generated label. Please handle with care.")
    c.drawString(margin, y_position - 0.15 * inch, f"Generated by SnapLive Logistics System")

    # Finalize PDF
    c.showPage()
    c.save()

    # Convert to base64 data URL
    pdf_bytes = buffer.getvalue()
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    return f"data:application/pdf;base64,{pdf_b64}"
