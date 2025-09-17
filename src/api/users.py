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
    return user


@router.patch(
    "/avatar", response_model=UserModel, dependencies=[Depends(change_avatar_access)]
)
async def update_avatar_user(
    file: UploadFile = File(),
    user: UserModel = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user_db = await user_service.update_avatar_url(user.email, avatar_url)

    return UserModel.model_validate(user_db)
