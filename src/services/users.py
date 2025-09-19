"""User service module.

Module provides business logic layer for user management operations.
It acts as an intermediary between the API layer and the repository layer,
handling user creation with Gravatar avatar integration.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas.schemas import UserCreate


class UserService:
    """Service class for user business logic operations.

    Provides high-level user management operations by coordinating
    with the user repository. Handles Gravatar integration and user operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the user service.

        Args:
            db (AsyncSession): Database session for repository operations
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """Create a new user with Gravatar avatar integration.

        Attempts to fetch a Gravatar image for the user's email address.
        Falls back to None if Gravatar is unavailable.

        Args:
            body (UserCreate): User registration data

        Returns:
            User: Created user object with assigned ID and avatar
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """Retrieve a user by their unique ID.

        Args:
            user_id (int): Unique identifier of the user

        Returns:
            User | None: User object if found, None otherwise
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """Retrieve a user by their username.

        Args:
            username (str): Username to search for

        Returns:
            User | None: User object if found, None otherwise
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """Retrieve a user by their email address.

        Args:
            email (str): Email address to search for

        Returns:
            User | None: User object if found, None otherwise
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """Mark a user's email as confirmed.

        Args:
            email (str): Email address to confirm

        Raises:
            ValueError: If user with email not found
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """Update a user's avatar URL.

        Args:
            email (str): Email of the user to update
            url (str): New avatar URL

        Returns:
            User: Updated user with new avatar URL

        Raises:
            ValueError: If user with email not found
        """
        return await self.repository.update_avatar_url(email, url)
