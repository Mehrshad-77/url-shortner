from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True
    )

    urls: Mapped[list["URL"]] = relationship(
        back_populates="user"
    )

    hashed_password: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True
    )

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True
    )

    short_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True
    )

    user: Mapped[User | None] = relationship(
        back_populates="urls"
    )