"""Email service module.

Module provides email functionality for the application including
email confirmation and password reset notifications using FastMail.

The module handles:
- Email configuration and connection setup
- Email confirmation messages with verification tokens
- Password reset email notifications
- HTML email templates with proper headers
"""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from starlette.datastructures import URL

from src.services.auth import AuthService
from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_confirm_email(
    email: EmailStr, username: str, host: URL, db=AsyncSession
):
    """Send email confirmation message to user with a verification token.

    Args:
        email (EmailStr): Recipient's email address
        username (str): Username for personalization
        host (URL): Base URL for constructing verification links
        db (AsyncSession): Database session for token creation

    Note:
        Silently handles connection errors to prevent application crashes
    """
    try:
        auth_service = AuthService(db)
        token_verification = await auth_service.create_email_token(data={"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
            headers={
                "List-Unsubscribe": "<mailto:unsubscribe@yourapp.com>",
                "X-Mailer": "Contacts App",
                "Reply-To": "no-reply@yourapp.com",
            },
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_password_reset_email(
    email: EmailStr, username: str, host: URL, token: str
):
    """Send password reset email to user with a reset link containing
    a secure token for password reset verification.

    Args:
        email (EmailStr): Recipient's email address
        username (str): Username for personalization
        host (URL): Base URL for constructing reset links
        token (str): Secure reset token for verification

    Note:
        Silently handles connection errors to prevent application crashes
    """
    try:
        reset_link = f"{str(host).rstrip('/')}/reset?token={token}"
        message = MessageSchema(
            subject="Password Reset Request - Contacts App",
            recipients=[email],
            template_body={"username": username, "reset_link": reset_link},
            subtype=MessageType.html,
            headers={
                "List-Unsubscribe": "<mailto:unsubscribe@yourapp.com>",
                "X-Mailer": "Contacts App",
                "Reply-To": "no-reply@yourapp.com",
            },
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password_email.html")
    except ConnectionErrors as err:
        print(f"Password reset email send failed: {err}")
