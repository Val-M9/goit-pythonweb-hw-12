import uuid
from datetime import date, timedelta
import pytest

from src.services.contacts import ContactService
from src.schemas.schemas import ContactModel, ContactUpdate
from tests.conftest import TestingAsyncSessionLocal


@pytest.mark.anyio
async def test_crud_and_search_contacts(user_model):
    async with TestingAsyncSessionLocal() as session:
        svc = ContactService(session)

        # Create two contacts
        c1 = await svc.create_contact(
            ContactModel(
                name="John",
                surname="Doe",
                email=f"john_{uuid.uuid4().hex[:8]}@example.com",
                phone_number=f"+1234567{uuid.uuid4().hex[:6]}",
                birthday=date.today(),
                additional_info="Friend",
            ),
            user_model,
        )
        c2 = await svc.create_contact(
            ContactModel(
                name="Jane",
                surname="Roe",
                email=f"jane_{uuid.uuid4().hex[:8]}@example.com",
                phone_number=f"+1987654{uuid.uuid4().hex[:6]}",
                birthday=date.today() + timedelta(days=1),
                additional_info="Colleague",
            ),
            user_model,
        )
        assert c1.id != c2.id

        # List with pagination
        lst = await svc.get_contacts(skip=0, limit=10, user=user_model)
        assert len(lst) >= 2

        # Search by name
        srch = await svc.get_contacts(skip=0, limit=10, user=user_model, query="Jane")
        assert any(x.id == c2.id for x in srch)

        # Get by id
        got = await svc.get_contact_by_id(c1.id, user_model)
        assert got and got.email == c1.email

        # Update
        upd = await svc.update_contact(
            c1.id, ContactUpdate(additional_info="Best friend"), user_model
        )
        assert upd and upd.additional_info == "Best friend"

        # Upcoming birthdays (next 2 days should include both)
        upcoming = await svc.get_contacts_with_upcoming_birthdays(2, user_model)
        ids = {x.id for x in upcoming}
        assert c1.id in ids and c2.id in ids

        # Delete
        deleted = await svc.delete_contact(c2.id, user_model)
        assert deleted and deleted.id == c2.id
        assert await svc.get_contact_by_id(c2.id, user_model) is None
