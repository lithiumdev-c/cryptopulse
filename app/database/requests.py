from re import U
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio.base import async_exc   
from app.database.models import Watchlist, async_session, User

from datetime import datetime, timedelta

async def set_user_id(user_id) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))

        if not user:
            session.add(User(user_id = user_id))
            await session.commit()

async def get_profile(user_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()  

async def get_active_subscribers(symbol: str, volume_usd: float) -> list:
    async with async_session() as session:
        query = (
            select(User)
            .join(Watchlist, User.user_id == Watchlist.user_id)
            .where(
                User.is_active == True,
                Watchlist.symbol == symbol,
                Watchlist.threshold_usd <= volume_usd
            )
        )

        result = await session.execute(query)
        return list(result.scalars().all())

async def get_user_watchlist(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Watchlist).where(Watchlist.user_id == user_id)
        )

        return result.scalars().all()

async def add_to_watchlist(user_id: int, symbol: str, threshold: float):
    async with async_session() as session:
        new_item = Watchlist(
            user_id = user_id,
            symbol = symbol.upper(),
            threshold_usd = threshold
        )
        session.add(new_item)
        await session.commit()

async def remove_from_watchlist(watchlist_id: int):
    async with async_session() as session:
        await session.execute(
            delete(Watchlist)
            .where(Watchlist.id == watchlist_id)
        )
        await session.commit()

async def toggle_user_status(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))
        if user:
            new_status = not user.is_active
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(is_active = new_status)
            )
            await session.commit()
            return new_status
        return False

async def get_watchlist_count(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Watchlist).where(Watchlist.user_id == user_id))
        return len(list(result.scalars().all()))

async def change_tier(user_id: int, days: int = 30):
    expires_at = datetime.utcnow() + timedelta(days=days)

    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(
                tier='premium',
                premium_expires_at = expires_at
            )
        )
        await session.commit()

async def expire_subscription() -> int:
    now = datetime.utcnow()
    async with async_session() as session:
        stmt = (
            update(User)
            .where(
                User.tier == 'premium',
                User.premium_expires_at <= now
            )
            .values(
                tier='free',
                premium_expires_at=None
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        return len(result.scalars().all())

async def get_all_monitored_symbols() -> list[str]:
    async with async_session() as session:
        result = await session.execute(select(Watchlist.symbol).distinct())
        return list(result.scalars().all())