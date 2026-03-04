"""
Mock Email Sender Utility

This module provides a mock email sender that logs emails to the console
and saves them to the database instead of actually sending them.
Replace this with a real email service (SendGrid, AWS SES, etc.) in production.
"""

import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MockEmailSender:
    """
    Mock email sender that logs emails and saves them to database
    instead of actually sending them.
    """

    def __init__(self, db: AsyncIOMotorDatabase, from_email: str = "noreply@snaplive.com"):
        """
        Initialize mock email sender

        Args:
            db: MongoDB database instance
            from_email: Sender email address
        """
        self.db = db
        self.from_email = from_email

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Send an email (mock implementation)

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            metadata: Additional metadata to store

        Returns:
            True if email was "sent" successfully, False otherwise
        """
        try:
            # Log to console with formatting
            logger.info("=" * 80)
            logger.info("📧 MOCK EMAIL SENT")
            logger.info("=" * 80)
            logger.info(f"From: {self.from_email}")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 80)
            logger.info("HTML Body Preview:")
            logger.info(html_body[:500] + "..." if len(html_body) > 500 else html_body)
            logger.info("=" * 80)

            # Save to database
            email_record = {
                "from_email": self.from_email,
                "to_email": to_email,
                "subject": subject,
                "html_body": html_body,
                "text_body": text_body,
                "metadata": metadata or {},
                "sent_at": datetime.utcnow(),
                "status": "sent",
                "is_mock": True
            }

            await self.db.sent_emails.insert_one(email_record)

            return True

        except Exception as e:
            logger.error(f"Failed to send mock email: {str(e)}")
            return False


class RealEmailSender:
    """
    Placeholder for real email sender implementation.

    To use a real email service:
    1. Install the appropriate library (sendgrid, boto3, etc.)
    2. Implement this class with the actual sending logic
    3. Update the configuration to use RealEmailSender instead of MockEmailSender
    """

    def __init__(self, api_key: str, from_email: str):
        """
        Initialize real email sender

        Args:
            api_key: API key for email service
            from_email: Sender email address
        """
        self.api_key = api_key
        self.from_email = from_email
        # TODO: Initialize email service client (SendGrid, AWS SES, etc.)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Send an email using real email service

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            metadata: Additional metadata

        Returns:
            True if email was sent successfully, False otherwise
        """
        # TODO: Implement actual email sending
        raise NotImplementedError("Real email sender not implemented yet")
