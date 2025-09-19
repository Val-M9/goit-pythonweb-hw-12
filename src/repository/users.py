"""User repository module.

Module provides data access layer for user management operations.
Handles all database interactions for user CRUD operations, authentication,
and profile management.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.schemas import UserCreate


class UserRepository:
    """Repository class for user data access operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the user repository.

        Args:
            session (AsyncSession): SQLAlchemy async database session
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by their unique ID.

        Args:
            user_id (int): Unique identifier of the user

        Returns:
            User | None: User if found, None otherwise
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username.

        Args:
            username (str): Username to search for

        Returns:
            User | None: User if found, None otherwise
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address.

        Args:
            email (str): Email address to search for

        Returns:
            User | None: User if found, None otherwise
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str | None = None) -> User:
        """Create a new user account.

        Args:
            body (UserCreate): User registration data
            avatar (str | None): Optional avatar URL

        Returns:
            User: The newly created user with assigned ID
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """Mark a user's email as confirmed.

        Args:
            email (str): Email address to confirm

        Raises:
            ValueError: If user with email not found
        """
        user = await self.get_user_by_email(email)
        if user is None:
            raise ValueError(f"User with email {email} not found")

        user.confirmed = True
        await self.db.commit()
        await self.db.refresh(user)

    async def update_avatar_url(self, email: str, url: str) -> User:
        """Update a user's avatar URL.

        Args:
            email (str): Email of the user to update
            url (str): New avatar URL

        Returns:
            User: Updated user with new avatar URL

        Raises:
            ValueError: If user with email not found
        """
        user = await self.get_user_by_email(email)
        if user is None:
            raise ValueError(f"User with email {email} not found")
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_password_by_email(self, email: str, hashed_password: str) -> None:
        """Update a user's password by email address.

        Args:
            email (str): Email of the user to update
            hashed_password (str): New hashed password

        Note:
            Silently returns if user not found (for security)
        """
        user = await self.get_user_by_email(email)
        if user is None:
            return
        user.hashed_password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
