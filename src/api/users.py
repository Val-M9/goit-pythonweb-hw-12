"""Users API module.

Module provides user management endpoints including profile retrieval
and avatar management functionality.

The module handles:
- User profile information retrieval
- Avatar upload and management (admin-only)
- Rate limiting for user endpoints
- Role-based access control
"""

from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.schemas import UserModel
from src.services.auth import get_current_user_dependency
from src.services.upload_file import UploadFileService
from src.services.users import UserService
from src.database.db import get_db
from src.database.models import Role
from src.conf.config import settings
from src.middlewares.limiter import limiter
from src.permissions.role_access import RoleAccess

router = APIRouter(prefix="/users", tags=["users"])

change_avatar_access = RoleAccess([Role.ADMIN])


@router.get("/me", response_model=UserModel)
@limiter.limit("10/minute")
async def me(request: Request, user: UserModel = Depends(get_current_user_dependency)):
    """Get current user's profile information.

    Args:
        request (Request): HTTP request object (required for rate limiting)
        user (UserModel): Authenticated user from JWT token

    Returns:
        UserModel: Current user's profile information
    """
    return user


@router.patch(
    "/avatar", response_model=UserModel, dependencies=[Depends(change_avatar_access)]
)
async def update_avatar_user(
    file: UploadFile = File(),
    user: UserModel = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """Update user's avatar image (Admin only).
    Uploads a new avatar image to Cloudinary and updates the user's profile
    with the new avatar URL.

    Args:
        file (UploadFile): Image file to upload as the new avatar
        user (UserModel): Authenticated user from JWT token
        db (AsyncSession): Database session dependency

    Returns:
        UserModel: Updated user profile with new avatar URL

    Permissions:
        Requires ADMIN role
    """
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user_db = await user_service.update_avatar_url(user.email, avatar_url)

    return UserModel.model_validate(user_db)
