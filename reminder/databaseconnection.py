from uuid import uuid4
from asyncpg import Connection
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from contextlib import asynccontextmanager
from models import *
import time


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

    async def get_notes_to_send(self) -> list[(str, int)]:
        """
        :return: list[(note_text, telegram_id)]
        """
        async with self.create_session() as session:
            stmt = select(
                Note.text, User.telegram_id
            ).where(
                Note.reminder_time.in_(range(int(time.time()) + 10 * 60 - 30, int(time.time()) + 10 * 60 + 31))
            ).join(
                User, User.id == Note.user_id
            )
            result = (await session.execute(stmt)).all()
            return result




