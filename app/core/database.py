"""
Database configuration and models for Supabase PostgreSQL
"""

import os
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from loguru import logger

Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    complexity_level = Column(String, default="medium")  # simple, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatSession(Base):
    """Модель сессии чата"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Message(Base):
    """Модель сообщения"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    sources = Column(Text, nullable=True)  # JSON string с источниками
    complexity_level = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def get_database_url() -> str:
    """Получить URL базы данных из переменных окружения"""
    # Supabase connection string
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback для разработки
        database_url = "postgresql://postgres:password@localhost:5432/eora_chatbot"
    
    return database_url

def create_database_engine_alternative():
    """Альтернативный способ создания engine с Transaction Pooler (IPv4 совместимый)"""
    try:
        # Используем DATABASE_URL как основной способ
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("❌ DATABASE_URL не найден в переменных окружения")
            return None
        
        # Добавляем параметры для Supabase если их нет
        if "?" not in database_url:
            database_url += "?sslmode=require&client_encoding=utf8"
        
        logger.info(f"🔧 Подключаемся к базе данных через DATABASE_URL")
        
        # Используем postgresql+psycopg2 как рекомендует Supabase
        engine = create_engine(database_url, echo=False)
        return engine
    except Exception as e:
        logger.error(f"Ошибка при создании альтернативного engine: {e}")
        return None

def create_database_engine():
    """Создать engine для подключения к базе данных"""
    database_url = get_database_url()
    # Добавляем параметры для Supabase
    if "?" not in database_url:
        database_url += "?sslmode=require&client_encoding=utf8"
    engine = create_engine(database_url, echo=False)
    return engine

def create_tables(engine):
    """Создать таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы базы данных созданы")

def get_session():
    """Получить сессию базы данных"""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal() 