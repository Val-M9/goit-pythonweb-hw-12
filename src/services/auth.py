"""Authentication service module.

Module provides comprehensive authentication services including password hashing,
JWT token management, user authentication, and Redis caching for user data.

The module handles:
- Password hashing and verification using bcrypt
- JWT token creation and validation for access, refresh, email, and reset tokens
- User authentication and authorization
- Redis caching for improved performance
- Token-based email confirmation and password reset
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Literal
import pickle

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt, ExpiredSignatureError
import redis

from src.database.db import get_db
from src.database.models import User
from src.conf.config import settings
from src.services.users import UserService
from src.conf.constants import TokenType


class Hash:
    """Password hashing utility class using bcrypt."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """Verify a plain password against its hash.

        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against

        Returns:
            bool: True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """Generate a bcrypt hash for a password.

        Args:
            password (str): Plain text password to hash

        Returns:
            str: Bcrypt hashed password
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """Authentication service for JWT token management and user authentication.

    Provides comprehensive authentication services including token creation,
    validation, user caching, and authentication workflows.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the authentication service.

        Args:
            db (AsyncSession): Database session for user operations
        """
        self.db = db
        self.redis_client = self._get_redis_client()
        self.user_service = UserService(db)

    def _get_redis_client(self):
        """Create and return Redis client for caching.

        Returns:
            redis.Redis: Configured Redis client instance
        """
        return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    async def _get_user_from_cache_or_db(self, username: str) -> User | None:
        """Get user from Redis cache or database, caching if found in DB"""
        # Try to get user from cache first
        cached_user = self.redis_client.get(f"user:{username}")
        if cached_user:
            return pickle.loads(cached_user)

        # If not in cache, get from database
        user = await self.user_service.get_user_by_username(username)
        if user:
            # Cache the user for 1 hour
            self.redis_client.set(f"user:{username}", pickle.dumps(user), ex=3600)

        return user

    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        """Extract and validate user from JWT access token.

        Args:
            token (str): JWT access token from Authorization header

        Returns:
            User: Authenticated user object

        Raises:
            HTTPException: 401 if token is invalid or user not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            username: str | None = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await self._get_user_from_cache_or_db(username)
        if user is None:
            raise credentials_exception

        return user

    def create_token(
        self,
        data: dict,
        expires_delta: timedelta,
        token_type: TokenType,
    ):
        """Create a JWT token with specified type and expiration.

        Args:
            data (dict): Payload data to encode in token
            expires_delta (timedelta): Token expiration time
            token_type: Type of token (access, refresh, email, reset)

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        now = datetime.now(UTC)
        expire = now + expires_delta
        to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        """Create an access token for API authentication.

        Args:
            data (dict): Token payload data
            expires_delta (Optional[timedelta]): Custom expiration (default: 15 minutes)

        Returns:
            str: JWT access token
        """
        if expires_delta:
            access_token = self.create_token(data, expires_delta, "access")
        else:
            access_token = self.create_token(data, timedelta(minutes=15), "access")
        return access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        """Create a refresh token for obtaining new access tokens.

        Args:
            data (dict): Token payload data
            expires_delta (Optional[timedelta]): Custom expiration (default: 7 days)

        Returns:
            str: JWT refresh token
        """
        if expires_delta:
            refresh_token = self.create_token(data, expires_delta, "refresh")
        else:
            refresh_token = self.create_token(
                data, timedelta(minutes=60 * 24 * 7), "refresh"
            )
        return refresh_token

    async def create_email_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        """Create a token for email confirmation.

        Args:
            data (dict): Token payload data
            expires_delta (Optional[timedelta]): Custom expiration (default: 15 minutes)

        Returns:
            str: JWT email confirmation token
        """
        if expires_delta:
            access_token = self.create_token(data, expires_delta, "email")
        else:
            access_token = self.create_token(data, timedelta(minutes=15), "email")
        return access_token

    def create_reset_password_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        """Create a token for password reset.

        Args:
            data (dict): Token payload data
            expires_delta (Optional[timedelta]): Custom expiration (default: 15 minutes)

        Returns:
            str: JWT password reset token
        """
        if expires_delta:
            access_token = self.create_token(data, expires_delta, "reset")
        else:
            access_token = self.create_token(data, timedelta(minutes=15), "reset")
        return access_token

    async def verify_refresh_token(self, refresh_token: str) -> User | None:
        """Verify and extract user from refresh token.

        Args:
            refresh_token (str): JWT refresh token to verify

        Returns:
            User | None: User object if token valid, None otherwise
        """
        try:
            payload = jwt.decode(
                refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            username: str | None = payload.get("sub")
            token_type: str | None = payload.get("token_type")
            if username is None or token_type != "refresh":
                return None

            user = await self._get_user_from_cache_or_db(username)
            return user
        except JWTError:
            return None

    async def get_email_from_token(self, token: str):
        """Extract email from email confirmation token.

        Args:
            token (str): JWT email confirmation token

        Returns:
            str: Email address from token

        Raises:
            HTTPException: 422 if token is invalid or wrong type
        """
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            email: str | None = payload.get("sub")
            token_type: str | None = payload.get("token_type")
            if not email or token_type != "email":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Token missing subject or invalid token type",
                )
            return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No correct token provided for email check",
            )

    async def get_email_from_reset_token(self, token: str):
        """Extract email from password reset token.

        Args:
            token (str): JWT password reset token

        Returns:
            str: Email address from token

        Raises:
            HTTPException: 401 if token expired, 422 if invalid
        """
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            email: str | None = payload.get("sub")
            token_type: str | None = payload.get("token_type")
            if not email or token_type != "reset":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Token missing subject or invalid token type",
                )
            return email
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid check",
            )


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency function to get AuthService instance.

    Args:
        db (AsyncSession): Database session dependency

    Returns:
        AuthService: Configured authentication service instance
    """
    return AuthService(db)


async def get_current_user_dependency(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI dependency to get current authenticated user.

    Args:
        token (str): JWT token from Authorization header
        db (AsyncSession): Database session dependency

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException: 401 if authentication fails
    """
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)
