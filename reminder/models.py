from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, Sequence, ForeignKey, BigInteger


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer,  Sequence('user_id', metadata=Base.metadata), primary_key=True)
    name = Column(String)
    email = Column(String)
    telegram_id = Column(Integer, unique=True, nullable=False)


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer,  Sequence('note_id', metadata=Base.metadata), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', onupdate='SET NULL', ondelete='SET NULL'))
    text = Column(String)
    reminder_time = Column(BigInteger)
