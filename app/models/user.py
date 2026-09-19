from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.avatar import DuckAvatar


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    # One of a fixed set of cartoon ducklings - see app/models/avatar.py.
    avatar: Mapped[DuckAvatar] = mapped_column(
        Enum(DuckAvatar, name="duck_avatar"),
        default=DuckAvatar.CLOVER,
        server_default=DuckAvatar.CLOVER.name,
    )
    # IANA timezone name, e.g. "Asia/Bangkok" - every streak calculation
    # converts UTC timestamps into this timezone before deciding on "today".
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Bangkok")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    habits: Mapped[list["Habit"]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )
