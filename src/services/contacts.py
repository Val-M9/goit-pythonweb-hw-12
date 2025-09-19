"""Contact service module.

Module provides business logic layer for contact management operations.
It acts as an intermediary between the API layer and the repository layer,
handling business rules and coordinating data operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.contacts import ContactRepository
from src.schemas.schemas import ContactModel, ContactUpdate


class ContactService:
    """Service class for contact business logic operations.

    Provides high-level contact management operations by coordinating
    with the contact repository. Handles business logic and validation.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the contact service.

        Args:
            db (AsyncSession): Database session for repository operations
        """
        self.contact_repository = ContactRepository(db)

    async def get_contacts(
        self, skip: int, limit: int, user: User, query: str | None = None
    ):
        """Retrieve paginated list of user's contacts with optional search.

        Args:
            skip (int): Number of records to skip for pagination
            limit (int): Maximum number of records to return
            user (User): User whose contacts to retrieve
            query (str | None): Optional search term for filtering

        Returns:
            List of contacts matching the criteria
        """
        return await self.contact_repository.get_contacts(skip, limit, user, query)

    async def get_contact_by_id(self, contact_id: int, user: User):
        """Retrieve a specific contact by ID.

        Args:
            contact_id (int): Unique identifier of the contact
            user (User): User who owns the contact

        Returns:
            Contact object if found and belongs to user, None otherwise
        """
        return await self.contact_repository.get_contact_by_id(contact_id, user)

    async def create_contact(self, body: ContactModel, user: User):
        """Create a new contact for the user.

        Args:
            body (ContactModel): Contact data to create
            user (User): User who will own the contact

        Returns:
            Created contact object with assigned ID
        """
        return await self.contact_repository.create_contact(body, user)

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User):
        """Update an existing contact with partial data.

        Args:
            contact_id (int): ID of the contact to update
            body (ContactUpdate): Partial contact data for updates
            user (User): User who owns the contact

        Returns:
            Updated contact object if found and belongs to user, None otherwise
        """
        return await self.contact_repository.update_contact(contact_id, body, user)

    async def delete_contact(self, contact_id: int, user: User):
        """Delete a contact permanently.

        Args:
            contact_id (int): ID of the contact to delete
            user (User): User who owns the contact

        Returns:
            Deleted contact object if found and belongs to user, None otherwise
        """
        return await self.contact_repository.delete_contact(contact_id, user)

    async def get_contacts_with_upcoming_birthdays(self, days: int, user: User):
        """Find contacts with birthdays in the next specified days.

        Args:
            days (int): Number of days ahead to search for birthdays
            user (User): User whose contacts to search

        Returns:
            List of contacts with upcoming birthdays
        """
        return await self.contact_repository.get_contacts_with_upcoming_birthdays(
            days, user
        )
