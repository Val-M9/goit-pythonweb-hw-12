import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.schemas import ContactModel, ContactUpdate


class MockContactRepository:
    def __init__(self, session):
        self.db = session

    def get_contacts(
        self, skip: int, limit: int, user: User, query: str | None = None
    ) -> list[Contact]:
        return []

    def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        return None

    def create_contact(self, contact: ContactModel, user: User) -> Contact:
        return Contact()

    def update_contact(
        self, contact_id: int, contact: ContactUpdate, user: User
    ) -> Contact | None:
        return None

    def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        return None

    def get_contacts_with_upcoming_birthdays(
        self, days: int, user: User
    ) -> list[Contact]:
        return []


@pytest.fixture
def mock_session():
    session = MagicMock(spec=AsyncSession)
    return session


@pytest.fixture
def contact_repository(mock_session):
    return MockContactRepository(mock_session)


@pytest.fixture
def sample_user():
    user = User()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password"
    user.confirmed = True
    return user


@pytest.fixture
def sample_contact(sample_user):
    contact = Contact()
    contact.id = 1
    contact.name = "John"
    contact.surname = "Doe"
    contact.email = "john.doe@example.com"
    contact.phone_number = "+1234567890"
    contact.birthday = date(1990, 1, 1)
    contact.additional_info = "Friend from work"
    contact.user_id = sample_user.id
    contact.user = sample_user
    return contact


@pytest.fixture
def contact_model():
    return ContactModel(
        name="John",
        surname="Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        birthday=date(1990, 1, 1),
        additional_info="Friend from work",
    )


@pytest.fixture
def contact_update():
    return ContactUpdate(additional_info="Updated info")


class TestContactRepository:
    def test_get_contacts_no_query(
        self, contact_repository, sample_user, sample_contact
    ):
        """Test retrieving contacts without search query."""
        with patch.object(
            contact_repository, "get_contacts", return_value=[sample_contact]
        ):
            result = contact_repository.get_contacts(skip=0, limit=10, user=sample_user)
            assert result == [sample_contact]

    def test_get_contacts_with_query(
        self, contact_repository, sample_user, sample_contact
    ):
        """Test retrieving contacts with search query."""
        with patch.object(
            contact_repository, "get_contacts", return_value=[sample_contact]
        ):
            result = contact_repository.get_contacts(
                skip=0, limit=10, user=sample_user, query="John"
            )
            assert result == [sample_contact]

    def test_get_contact_by_id_found(
        self, contact_repository, sample_user, sample_contact
    ):
        """Test retrieving a contact by ID when found."""
        with patch.object(
            contact_repository, "get_contact_by_id", return_value=sample_contact
        ):
            result = contact_repository.get_contact_by_id(1, sample_user)
            assert result == sample_contact

    def test_get_contact_by_id_not_found(self, contact_repository, sample_user):
        """Test retrieving a contact by ID when not found."""
        with patch.object(contact_repository, "get_contact_by_id", return_value=None):
            result = contact_repository.get_contact_by_id(999, sample_user)
            assert result is None

    def test_create_contact(
        self, contact_repository, sample_user, contact_model, sample_contact
    ):
        """Test creating a new contact."""
        with patch.object(
            contact_repository, "create_contact", return_value=sample_contact
        ):
            result = contact_repository.create_contact(contact_model, sample_user)
            assert result == sample_contact

    def test_update_contact_found(
        self, contact_repository, sample_user, contact_update, sample_contact
    ):
        """Test updating a contact when found."""
        with patch.object(
            contact_repository, "update_contact", return_value=sample_contact
        ):
            result = contact_repository.update_contact(1, contact_update, sample_user)
            assert result == sample_contact

    def test_update_contact_not_found(
        self, contact_repository, sample_user, contact_update
    ):
        """Test updating a contact when not found."""
        with patch.object(contact_repository, "update_contact", return_value=None):
            result = contact_repository.update_contact(999, contact_update, sample_user)
            assert result is None

    def test_delete_contact_found(
        self, contact_repository, sample_user, sample_contact
    ):
        """Test deleting a contact when found."""
        with patch.object(
            contact_repository, "delete_contact", return_value=sample_contact
        ):
            result = contact_repository.delete_contact(1, sample_user)
            assert result == sample_contact

    def test_delete_contact_not_found(self, contact_repository, sample_user):
        """Test deleting a contact when not found."""
        with patch.object(contact_repository, "delete_contact", return_value=None):
            result = contact_repository.delete_contact(999, sample_user)
            assert result is None

    def test_get_contacts_with_upcoming_birthdays(
        self, contact_repository, sample_user, sample_contact
    ):
        """Test finding contacts with upcoming birthdays."""
        with patch.object(
            contact_repository,
            "get_contacts_with_upcoming_birthdays",
            return_value=[sample_contact],
        ):
            result = contact_repository.get_contacts_with_upcoming_birthdays(
                7, sample_user
            )
            assert isinstance(result, list)

    def test_get_contacts_with_upcoming_birthdays_no_contacts(
        self, contact_repository, sample_user
    ):
        """Test finding contacts with upcoming birthdays when no contacts exist."""
        with patch.object(
            contact_repository, "get_contacts_with_upcoming_birthdays", return_value=[]
        ):
            result = contact_repository.get_contacts_with_upcoming_birthdays(
                7, sample_user
            )
            assert result == []
