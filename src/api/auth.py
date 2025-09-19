"""Authentication API module.

Module provides authentication-related endpoints including user registration,
login, email confirmation, token refresh, and password reset functionality.

The module handles:
- User registration with email confirmation
- User login with JWT token generation
- Email confirmation workflow
- JWT token refresh mechanism
- Password reset via email

"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from src.schemas.schemas import (
    UserCreate,
    TokenModel,
    UserModel,
    RequestEmail,
    TokenRefreshRequest,
    ForgotPasswordBody,
    ResetPasswordBody,
)
from src.services.auth import (
    AuthService,
    get_auth_service,
    Hash,
)
from src.services.users import UserService
from src.services.email import send_confirm_email, send_password_reset_email
from src.database.db import get_db
from src.database.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserModel, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user.

    Creates a new user account with email and username validation.
    Sends a confirmation email in the background.

    Args:
        user_data (UserCreate): User registration data including email, username, and password
        background_tasks (BackgroundTasks): FastAPI background tasks for email sending
        request (Request): HTTP request object for base URL extraction
        db (AsyncSession): Database session dependency

    Returns:
        UserModel: The created user data (without password)

    Raises:
        HTTPException: 409 if email or username already exists
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this name already exists",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)

    background_tasks.add_task(
        send_confirm_email, new_user.email, new_user.username, request.base_url, db
    )

    return new_user


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_200_OK)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return JWT tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): Login form with username and password
        db (AsyncSession): Database session dependency
        auth_service (AuthService): Authentication service dependency

    Returns:
        TokenModel: Access token, refresh token, and token type

    Raises:
        HTTPException: 401 if credentials are invalid or email not confirmed
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not confirmed",
        )

    access_token = await auth_service.create_access_token(data={"sub": user.username})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Confirm user email address using verification token.

    Validates the email confirmation token and marks the user's email as confirmed.

    Args:
        token (str): Email confirmation token from the verification link
        db (AsyncSession): Database session dependency
        auth_service (AuthService): Authentication service dependency

    Returns:
        dict: Success message indicating email confirmation status

    Raises:
        HTTPException: 400 if token is invalid or user not found
    """
    email = await auth_service.get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Email already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email is not confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Request email confirmation resend.

    Args:
        body (RequestEmail): Request body containing the email address
        background_tasks (BackgroundTasks): FastAPI background tasks for email sending
        request (Request): HTTP request object for base URL extraction
        db (AsyncSession): Database session dependency

    Returns:
        dict: Success message asking user to check their email
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user and user.confirmed:
        return {"message": "Email already confirmed"}
    if user:
        background_tasks.add_task(
            send_confirm_email, user.email, user.username, request.base_url
        )
    return {"message": "Please check your email for confirmation"}


@router.post("/refresh-token", response_model=TokenModel)
async def new_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh JWT access token using refresh token.

    Args:
        request (TokenRefreshRequest): Request body containing the refresh token
        db (AsyncSession): Database session dependency
        auth_service (AuthService): Authentication service dependency

    Returns:
        TokenModel: New access token with the same refresh token
    """
    user: User | None = await auth_service.verify_refresh_token(request.refresh_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    new_access_token = await auth_service.create_access_token(
        data={"sub": user.username}
    )
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.post("/password/forgot")
async def forgot_password(
    body: ForgotPasswordBody,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
):
    """Initiate password reset process.
    Sends a password reset email with a secure token to the user's email address.

    Args:
        body (ForgotPasswordBody): Request body containing the email address
        background_tasks (BackgroundTasks): FastAPI background tasks for email sending
        request (Request): HTTP request object for base URL extraction
        db (AsyncSession): Database session dependency
        auth (AuthService): Authentication service dependency

    Returns:
        dict: Success message indicating reset link was sent
    """
    user = await UserService(db).get_user_by_email(body.email)
    if user:
        token = auth.create_reset_password_token({"sub": body.email})
        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            user.username,
            request.base_url,
            token,
        )
    return {"message": "Reset link was sent"}


@router.post("/password/reset")
async def reset_password(
    body: ResetPasswordBody,
    db: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
):
    """Reset user password using reset token.

    Args:
        body (ResetPasswordBody): Request body containing reset token and new password
        db (AsyncSession): Database session dependency
        auth (AuthService): Authentication service dependency

    Returns:
        dict: Success message indicating password was updated
    """
    try:
        email = await auth.get_email_from_reset_token(body.token)
    except Exception:
        # Invalid or expired reset token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    hashed = Hash().get_password_hash(body.new_password)
    await UserService(db).repository.update_password_by_email(email, hashed)
    return {"message": "Password updated"}
