from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker
from sqlalchemy import create_engine, MetaData, Column, Integer, String, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from config import db_path

engine = create_engine(f'sqlite:///{db_path}', echo=False,
                       connect_args={"check_same_thread": False})
conn = engine.connect()

class Base(DeclarativeBase):
    pass


class DataDb(Base):
    __tablename__ = "Data"
    id: Mapped[int] = mapped_column(primary_key=True)
    manufacruter: Mapped[str] = mapped_column()
    number: Mapped[str] = mapped_column()
    price: Mapped[str] = mapped_column()
    link: Mapped[str] = mapped_column()



