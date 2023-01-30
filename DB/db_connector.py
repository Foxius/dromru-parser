from typing import Optional
from sqlalchemy import create_engine, MetaData, Column, Integer, String, DateTime, ForeignKey
import sqlalchemy as db
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from .models import Base, engine


Base.metadata.create_all(engine)
SessionDb = sessionmaker(bind=engine)()
SessionDb.autoflush = False

