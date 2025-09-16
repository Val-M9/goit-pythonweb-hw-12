from datetime import date, datetime
import enum

from sqlalchemy import Integer, String, Date, Boolean, func, ForeignKey, Enum
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from sqlalchemy.sql.sqltypes import DateTime


class Base(DeclarativeBase):
    pass


class Role(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    surname: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True)
    birthday: Mapped[date] = mapped_column(Date)
    additional_info: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="user")
    confirmed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    role: Mapped[Role] = mapped_column(
        Enum(Role, values_callable=lambda enum_cls: [e.value for e in enum_cls], name="role"),
        default=Role.USER,
    )
