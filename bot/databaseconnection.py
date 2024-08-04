import time
from uuid import uuid4
from asyncpg import Connection
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import or_, func
from contextlib import asynccontextmanager

from models import *


class CConnection(Connection):
    def _get_unique_id(self, prefix: str) -> str:
        return f'__asyncpg_{prefix}_{uuid4()}__'


class DataBaseWorker:
    def __init__(self, host, port, user, password, database):
        try:
            self.engine = create_async_engine(
                f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                    "connection_class": CConnection,
                }
            )
            self.connection = self.engine.connect()
            self.session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        except Exception as e:
            print("Ошибка при подключении к БД", e)

        self.session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def connect(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()

    @asynccontextmanager
    async def create_session(self):
        async with self.session() as db:
            try:
                yield db
            except:
                await db.rollback()
                raise
            finally:
                await db.close()

    async def is_user_exists(self, user_id: int = None, telegram_id: int = None) -> bool:
        if user_id is None and telegram_id is None:
            raise Exception("You must provide either user_id or telegram_id")
        async with self.create_session() as session:
            stmt = select(User).where(or_(User.id == user_id, User.telegram_id == telegram_id))
            result = (await session.execute(stmt)).all()
            return bool(len(result))

    async def get_id_by_telegram_id(self, telegram_id: int) -> int:
        async with self.create_session() as session:
            stmt = select(User.id).where(User.telegram_id == telegram_id)
            result = (await session.execute(stmt)).scalars().first()
            return result

    async def new_user(self, name: str, email: str, telegram_id: int) -> None:
        async with self.create_session() as session:
            session.add(
                User(
                    name=name,
                    email=email,
                    telegram_id=telegram_id
                )
            )
            await session.commit()

    async def is_note_exists(self, note_id: int) -> bool:
        async with self.create_session() as session:
            stmt = select(Note).where(Note.id == note_id)
            result = (await session.execute(stmt)).all()
            return bool(len(result))

    async def new_note(self, user_id: int, text: str, reminder_time: int) -> None:
        if not await self.is_user_exists(user_id=user_id):
            raise Exception(f"No such user: {user_id}")
        if reminder_time < time.time():
            raise Exception("Incorrect date")
        async with self.create_session() as session:
            session.add(
                Note(
                    user_id=user_id,
                    text=text,
                    reminder_time=reminder_time
                )
            )
            await session.commit()

    async def get_user_notes(self, user_id: int, limit: int = 10, offset: int = 0) -> list[Note]:
        async with self.create_session() as session:
            stmt = select(Note).where(Note.user_id == user_id).order_by(Note.reminder_time).limit(limit).offset(offset)
            result = (await session.execute(stmt)).scalars().all()
            return result

    async def user_notes_count(self, user_id: int) -> int:
        async with self.create_session() as session:
            stmt = select(func.count(Note.id)).where(Note.user_id == user_id)
            num = int((await session.execute(stmt)).scalar())
            return num

    async def get_note(self, note_id: int) -> Note:
        if not await self.is_note_exists(note_id=note_id):
            raise Exception(f"No such note: {note_id}")
        async with self.create_session() as session:
            stmt = select(Note).where(Note.id == note_id)
            result = (await session.execute(stmt)).scalars().first()
            return result




