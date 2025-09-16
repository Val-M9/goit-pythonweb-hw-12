from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, SecretStr


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/contacts_db"
    JWT_SECRET: str = "your_jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600

    MAIL_USERNAME: EmailStr = "email@example.com"
    MAIL_PASSWORD: SecretStr = "password"  # type: ignore
    MAIL_FROM: EmailStr = "email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Contacts App"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLOUDINARY_NAME: str = "cloud_name"
    CLOUDINARY_API_KEY: str = "123456789"
    CLOUDINARY_API_SECRET: str = "cloudinary_api_secret"

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()  # type: ignore
