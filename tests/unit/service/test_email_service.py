import pytest
from starlette.datastructures import URL

from src.services.email import send_confirm_email, send_password_reset_email
from src.services.auth import AuthService
from tests.conftest import TestingAsyncSessionLocal


class DummyFastMail:
    def __init__(self, conf):
        self.conf = conf
        self.sent = []

    async def send_message(self, message, template_name: str):
        # Record the message content for assertions
        self.sent.append({
            "subject": message.subject,
            "recipients": message.recipients,
            "template_body": message.template_body,
            "headers": message.headers,
            "template_name": template_name,
        })


@pytest.mark.anyio
async def test_send_confirm_email(monkeypatch):
    # Avoid real Redis usage during AuthService init
    monkeypatch.setattr(AuthService, "_get_redis_client", lambda self: None)

    # Patch FastMail to our dummy recorder
    import src.services.email as email_module
    dummy = DummyFastMail(email_module.conf)
    monkeypatch.setattr(email_module, "FastMail", lambda conf: dummy)

    async with TestingAsyncSessionLocal() as session:
        host = URL("http://testserver")
        await send_confirm_email(
            email="confirm@example.com",
            username="confirm_user",
            host=host,
            db=session,
        )

    assert len(dummy.sent) == 1
    sent = dummy.sent[0]
    assert sent["template_name"] == "verify_email.html"
    assert sent["recipients"] == ["confirm@example.com"]
    assert sent["subject"].lower().startswith("confirm")
    assert sent["template_body"]["username"] == "confirm_user"
    assert "token" in sent["template_body"] and isinstance(sent["template_body"]["token"], str)


@pytest.mark.anyio
async def test_send_password_reset_email(monkeypatch):
    import src.services.email as email_module
    dummy = DummyFastMail(email_module.conf)
    monkeypatch.setattr(email_module, "FastMail", lambda conf: dummy)

    host = URL("http://example.org")
    await send_password_reset_email(
        email="reset@example.com",
        username="reset_user",
        host=host,
        token="abc123",
    )

    assert len(dummy.sent) == 1
    sent = dummy.sent[0]
    assert sent["template_name"] == "reset_password_email.html"
    assert sent["recipients"] == ["reset@example.com"]
    assert sent["subject"].lower().startswith("password reset")
    assert sent["template_body"]["username"] == "reset_user"
    assert sent["template_body"]["reset_link"] == "http://example.org/reset?token=abc123"
