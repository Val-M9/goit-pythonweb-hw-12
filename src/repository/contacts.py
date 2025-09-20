"""Contact repository module.

Module provides data access layer for contact management operations.
Handles all database interactions for contact CRUD operations and search functionality.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import date

from src.database.models import Contact, User
from src.schemas.schemas import ContactModel, ContactUpdate


class ContactRepository:
    """Repository class for contact data access operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the contact repository.

        Args:
            session (AsyncSession): SQLAlchemy async database session
        """
        self.db = session

    async def get_contacts(
        self, skip: int, limit: int, user: User, query: str | None = None
    ) -> list[Contact]:
        """Retrieve paginated list of user's contacts with optional search.

        Args:
            skip (int): Number of records to skip for pagination
            limit (int): Maximum number of records to return
            user (User): User whose contacts to retrieve
            query (str | None): Optional search term for name, surname, or email

        Returns:
            list[Contact]: List of contacts matching the criteria
        """
        stmt = select(Contact).filter_by(user=user).offset(skip).limit(limit)

        if query:
            search = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Contact.name.ilike(search),
                    Contact.surname.ilike(search),
                    Contact.email.ilike(search),
                )
            )

        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()  # pyright: ignore[reportReturnType]

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """Retrieve a specific contact by ID for a user.

        Args:
            contact_id (int): Unique identifier of the contact
            user (User): User who owns the contact

        Returns:
            Contact | None: Contact if found and belongs to user, None otherwise
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact | None:
        """Create a new contact for a user.

        Args:
            body (ContactModel): Contact data to create
            user (User): User who will own the contact

        Returns:
            Contact | None: The created contact with assigned ID
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return await self.get_contact_by_id(contact.id, user)

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        """Update an existing contact with partial data.

        Args:
            contact_id (int): ID of the contact to update
            body (ContactUpdate): Partial contact data for updates
            user (User): User who owns the contact

        Returns:
            Contact | None: Updated contact if found and belongs to user, None otherwise
        """
        contact = await self.get_contact_by_id(contact_id, user)

        if contact:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, field, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        """Delete a contact permanently.

        Args:
            contact_id (int): ID of the contact to delete
            user (User): User who owns the contact

        Returns:
            Contact | None: Deleted contact data if found and belongs to user, None otherwise
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:            
            await self.db.delete(contact)
            await self.db.commit()
            return contact
        return None

    async def get_contacts_with_upcoming_birthdays(
        self, days: int, user: User
    ) -> list[Contact] | None:
        """Find contacts with birthdays in the next specified days.

        Calculates upcoming birthdays considering year transitions.

        Args:
            days (int): Number of days ahead to search for birthdays
            user (User): User whose contacts to search

        Returns:
            list[Contact] | None: List of contacts with upcoming birthdays
        """
        today = date.today()

        stmt = select(Contact).filter_by(user=user)
        result = await self.db.execute(stmt)
        all_contacts = result.scalars().all()

        upcoming__contacts_birthdays = []

        for contact in all_contacts:
            if contact.birthday:
                birthday_this_year = contact.birthday.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = contact.birthday.replace(year=today.year + 1)

                days_until_birthday = (birthday_this_year - today).days

                if 0 <= days_until_birthday <= days:
                    upcoming__contacts_birthdays.append(contact)

        return upcoming__contacts_birthdays
