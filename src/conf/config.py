from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr, SecretStr


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/contacts_db"
    )

    @property
    def DB_URL(self) -> str:
        # Normalize URL for SQLAlchemy async engine with asyncpg
        url = self.DATABASE_URL
        # Normalize scheme aliases and ensure asyncpg driver
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]

        # Convert sslmode to asyncpg-compatible params (ssl)
        try:
            from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

            parts = urlsplit(url)
            query_pairs = dict(parse_qsl(parts.query, keep_blank_values=True))
            sslmode = query_pairs.get("sslmode")
            if sslmode:
                # asyncpg does not accept sslmode; use ssl=true for require/prefer
                if sslmode.lower() in {"require", "verify-ca", "verify-full", "prefer"}:
                    query_pairs.pop("sslmode", None)
                    # set ssl=true only if not explicitly disabled
                    query_pairs.setdefault("ssl", "true")
                elif sslmode.lower() in {"disable"}:
                    query_pairs.pop("sslmode", None)
                    query_pairs["ssl"] = "false"
            else:
                # Neon usually requires SSL; default to ssl=true if host ends with neon.tech
                if parts.hostname and parts.hostname.endswith("neon.tech"):
                    query_pairs.setdefault("ssl", "true")

            new_query = urlencode(query_pairs, doseq=True)
            url = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, new_query, parts.fragment)
            )
        except Exception:
            # If parsing fails, just return the best-effort url
            pass

        return url

    JWT_SECRET: str = "your_jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    MAIL_USERNAME: EmailStr = "email@example.com"
    MAIL_PASSWORD: SecretStr = "password"
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


settings = Settings()
