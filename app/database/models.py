from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String   
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(
    url=DATABASE_URL,
    echo=False
)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tier: Mapped[str] = mapped_column(String(20), default="free")
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    watchlist: Mapped[list["Watchlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    premium_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold_usd: Mapped[float] = mapped_column(default=1000000.0)
    user: Mapped["User"] = relationship(back_populates="watchlist")

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

