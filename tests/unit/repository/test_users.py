import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.schemas import UserCreate


class MockUserRepository:
    def __init__(self, session):
        self.db = session

    def get_user_by_id(self, user_id: int) -> User | None:
        return None

    def get_user_by_username(self, username: str) -> User | None:
        return None

    def get_user_by_email(self, email: str) -> User | None:
        return None

    def create_user(self, user: UserCreate, avatar: str | None) -> User:
        return User()

    def confirmed_email(self, email: str) -> None:
        pass

    def update_avatar_url(self, email: str, url: str) -> User:
        return User()

    def update_password_by_email(self, email: str, hashed_password: str) -> None:
        pass


@pytest.fixture
def mock_session():
    """Mock AsyncSession for testing."""
    session = MagicMock(spec=AsyncSession)
    return session


@pytest.fixture
def user_repository(mock_session):
    return MockUserRepository(mock_session)


@pytest.fixture
def user_create():
    return UserCreate(
        username="newuser", email="newuser@example.com", password="hashed_password"
    )


class TestUserRepository:
    def test_get_user_by_id_found(self, user_repository, user):
        """Test retrieving a user by ID when found."""
        with patch.object(user_repository, "get_user_by_id", return_value=user):
            result = user_repository.get_user_by_id(1)
            assert result == user

    def test_get_user_by_id_not_found(self, user_repository):
        """Test retrieving a user by ID when not found."""
        with patch.object(user_repository, "get_user_by_id", return_value=None):
            result = user_repository.get_user_by_id(999)
            assert result is None

    def test_get_user_by_username_found(self, user_repository, user):
        """Test retrieving a user by username when found."""
        with patch.object(user_repository, "get_user_by_username", return_value=user):
            result = user_repository.get_user_by_username("testuser")
            assert result == user

    def test_get_user_by_username_not_found(self, user_repository):
        """Test retrieving a user by username when not found."""
        with patch.object(user_repository, "get_user_by_username", return_value=None):
            result = user_repository.get_user_by_username("nonexistent")
            assert result is None

    def test_get_user_by_email_found(self, user_repository, user):
        """Test retrieving a user by email when found."""
        with patch.object(user_repository, "get_user_by_email", return_value=user):
            result = user_repository.get_user_by_email("test@example.com")
            assert result == user

    def test_get_user_by_email_not_found(self, user_repository):
        """Test retrieving a user by email when not found."""
        with patch.object(user_repository, "get_user_by_email", return_value=None):
            result = user_repository.get_user_by_email("nonexistent@example.com")
            assert result is None

    def test_create_user(self, user_repository, user_create, user):
        """Test creating a new user."""
        with patch.object(user_repository, "create_user", return_value=user):
            result = user_repository.create_user(
                user_create, "https://example.com/avatar.jpg"
            )
            assert result == user

    def test_create_user_no_avatar(self, user_repository, user_create, user):
        """Test creating a new user without avatar."""
        with patch.object(user_repository, "create_user", return_value=user):
            result = user_repository.create_user(user_create, None)
            assert result == user

    def test_confirmed_email_success(self, user_repository, user):
        """Test confirming email for existing user."""
        with patch.object(
            user_repository, "confirmed_email", return_value=None
        ) as mock_confirmed:
            user_repository.confirmed_email("test@example.com")
            mock_confirmed.assert_called_once_with("test@example.com")

    def test_confirmed_email_user_not_found(self, user_repository):
        """Test confirming email for non-existent user."""
        with patch.object(
            user_repository,
            "confirmed_email",
            side_effect=ValueError("User with email nonexistent@example.com not found"),
        ):
            with pytest.raises(
                ValueError, match="User with email nonexistent@example.com not found"
            ):
                user_repository.confirmed_email("nonexistent@example.com")

    def test_update_avatar_url_success(self, user_repository, user):
        """Test updating avatar URL for existing user."""
        with patch.object(user_repository, "update_avatar_url", return_value=user):
            result = user_repository.update_avatar_url(
                "test@example.com", "https://new-avatar.com/image.jpg"
            )
            assert result == user

    def test_update_avatar_url_user_not_found(self, user_repository):
        """Test updating avatar URL for non-existent user."""
        with patch.object(
            user_repository,
            "update_avatar_url",
            side_effect=ValueError("User with email nonexistent@example.com not found"),
        ):
            with pytest.raises(
                ValueError, match="User with email nonexistent@example.com not found"
            ):
                user_repository.update_avatar_url(
                    "nonexistent@example.com", "https://new-avatar.com/image.jpg"
                )

    def test_update_password_by_email_success(self, user_repository, user):
        """Test updating password for existing user."""
        with patch.object(
            user_repository, "update_password_by_email", return_value=None
        ) as mock_update:
            user_repository.update_password_by_email(
                "test@example.com", "new_hashed_password"
            )
            mock_update.assert_called_once_with(
                "test@example.com", "new_hashed_password"
            )

    def test_update_password_by_email_user_not_found(self, user_repository):
        """Test updating password for non-existent user."""
        with patch.object(
            user_repository, "update_password_by_email", return_value=None
        ) as mock_update:
            user_repository.update_password_by_email(
                "nonexistent@example.com", "new_hashed_password"
            )
            mock_update.assert_called_once_with(
                "nonexistent@example.com", "new_hashed_password"
            )
