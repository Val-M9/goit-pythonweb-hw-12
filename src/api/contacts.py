"""Contacts API module.

Module provides CRUD operations for managing user contacts.
All endpoints require user authentication and operate on user-specific data.

The module handles:
- Creating, reading, updating, and deleting contacts
- Searching contacts by name, surname, or email
- Finding contacts with upcoming birthdays
- Pagination support for contact listings
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database.db import get_db
from src.database.models import User
from src.schemas.schemas import (
    ContactResponse,
    ContactModel,
    ContactUpdate,
    BirthdaysResponse,
)
from src.services.auth import get_current_user_dependency
from src.services.contacts import ContactService


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def read_contacts(
    skip: int = 0,
    limit: int = 50,
    query: Optional[str] = Query(None, description="Search by name, surname or email"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """Retrieve user's contacts with optional search and pagination.

    Args:
        skip (int): Number of records to skip for pagination (default: 0)
        limit (int): Maximum number of records to return (default: 50)
        query (Optional[str]): Search term to filter contacts by name, surname, or email
        db (AsyncSession): Database session dependency
        user (User): Authenticated user from JWT token

    Returns:
        list[ContactResponse]: List of user's contacts matching the criteria
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts(skip, limit, user, query)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """Retrieve a specific contact by ID.

    Args:
        contact_id (int): Unique identifier of the contact to retrieve
        db (AsyncSession): Database session dependency
        user (User): Authenticated user from JWT token

    Returns:
        ContactResponse: The requested contact's details

    Raises:
        HTTPException: 404 if contact not found or doesn't belong to user
    """
    contact_service = ContactService(db)
    contact = await contact_service.get_contact_by_id(contact_id, user)
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """Create a new contact for the authenticated user.

    Args:
        body (ContactModel): Contact data including name, surname, email, phone, birthday, etc.
        db (AsyncSession): Database session dependency
        user (User): Authenticated user from JWT token

    Returns:
        ContactResponse: The newly created contact with assigned ID

    Raises:
        HTTPException: 400 if validation fails or contact data is invalid
    """
    contact_service = ContactService(db)
    return await contact_service.create_contact(body, user)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactUpdate,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """Update an existing contact with partial data.
    Updates specific fields of an existing contact using PATCH semantics.

    Args:
        body (ContactUpdate): Partial contact data with fields to update
        contact_id (int): Unique identifier of the contact to update
        db (AsyncSession): Database session dependency
        user (User): Authenticated user from JWT token

    Returns:
        ContactResponse: The updated contact with all current data

    Raises:
        HTTPException: 404 if contact not found or doesn't belong to user
    """
    contact_service = ContactService(db)
    contact = await contact_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """Delete a contact permanently.

    Args:
        contact_id (int): Unique identifier of the contact to delete
        db (AsyncSession): Database session dependency
        user (User): Authenticated user from JWT token

    Returns:
        ContactResponse: The deleted contact's data for confirmation

    Raises:
        HTTPException: 404 if contact not found or doesn't belong to user
    """
    contact_service = ContactService(db)
    contact = await contact_service.delete_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.get("/upcoming_birthdays/", response_model=BirthdaysResponse)
async def read_contacts_with_upcoming_birthdays(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """Find contacts with upcoming birthdays.

    Returns contacts whose birthdays fall within the specified number of days
    from today.

    Args:
        days (int): Number of days ahead to search for birthdays (default: 7)
        db (AsyncSession): Database session dependency
        user (User): Authenticated user from JWT token

    Returns:
        BirthdaysResponse: Response containing message and list of contacts with upcoming birthdays
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts_with_upcoming_birthdays(days, user)
    if not contacts:
        return BirthdaysResponse(
            message="No birthdays this week",
            contacts=[],
        )

    contact_responses = [
        ContactResponse.model_validate(contact) for contact in contacts
    ]

    return BirthdaysResponse(
        message="Birthdays this week",
        contacts=contact_responses,
    )
