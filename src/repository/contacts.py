from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, extract
from datetime import date

from src.database.models import Contact, User
from src.schemas.schemas import ContactModel, ContactUpdate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(
        self, skip: int, limit: int, user: User, query: str | None = None
    ) -> list[Contact]:
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
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact | None:
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return await self.get_contact_by_id(contact.id, user)

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)

        if contact:
            for field, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, field, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def get_contacts_with_upcoming_birthdays(
        self, days: int, user: User
    ) -> list[Contact] | None:
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
