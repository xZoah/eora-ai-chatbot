"""
Database service for Supabase integration
"""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger
import os

from app.core.database import (
    User, ChatSession, Message, 
    get_session, create_tables, create_database_engine, create_database_engine_alternative
)


class DatabaseService:
    """Сервис для работы с базой данных"""
    
    def __init__(self):
        self.engine = None
        self.session = None
        
    def initialize(self) -> bool:
        """Инициализировать подключение к базе данных"""
        try:
            logger.info("🔧 Инициализируем подключение к Supabase...")
            
            # Проверяем наличие переменных окружения
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                logger.warning("⚠️ DATABASE_URL не найден, приложение будет работать без базы данных")
                return False
            
            # Используем Transaction Pooler (IPv4 совместимый) как основной способ
            self.engine = create_database_engine_alternative()
            if not self.engine:
                logger.warning("⚠️ Transaction Pooler не сработал, пробуем Direct Connection...")
                # Fallback на основной способ
                self.engine = create_database_engine()
                if not self.engine:
                    logger.error("❌ Не удалось подключиться к базе данных")
                    return False
                logger.info("✅ Direct Connection успешен")
            else:
                logger.info("✅ Transaction Pooler подключение успешно")
            
            # Создаем таблицы если их нет
            create_tables(self.engine)
            
            # Создаем сессию из нашего engine
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.session = SessionLocal()
            logger.success("✅ Подключение к Supabase успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
            return False
    
    def get_or_create_user(self, telegram_id: str, username: str = None, 
                          first_name: str = None, last_name: str = None) -> Optional[User]:
        """Получить пользователя или создать нового"""
        try:
            if not self.session:
                logger.warning("⚠️ База данных не инициализирована")
                return None
                
            # Ищем существующего пользователя
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            
            if user:
                # Обновляем информацию если нужно
                if username and user.username != username:
                    user.username = username
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                self.session.commit()
            else:
                # Создаем нового пользователя
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    complexity_level="hard"  # По умолчанию
                )
                self.session.add(user)
                self.session.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"Ошибка при работе с пользователем: {e}")
            if self.session:
                self.session.rollback()
            return None
    
    def update_user_complexity(self, telegram_id: str, complexity_level: str) -> bool:
        """Обновить уровень сложности пользователя"""
        try:
            if not self.session:
                logger.warning("⚠️ База данных не инициализирована")
                return False
                
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.complexity_level = complexity_level
                self.session.commit()
                logger.info(f"👤 Пользователь {telegram_id}: уровень сложности изменен на {complexity_level}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении уровня сложности: {e}")
            if self.session:
                self.session.rollback()
            return False
    
    def create_chat_session(self, user_id: int) -> Optional[ChatSession]:
        """Создать новую сессию чата"""
        try:
            if not self.session:
                logger.warning("⚠️ База данных не инициализирована")
                return None
                
            import uuid
            session_id = str(uuid.uuid4())
            
            session = ChatSession(
                user_id=user_id,
                session_id=session_id
            )
            self.session.add(session)
            self.session.commit()
            
            logger.info(f"💬 Создана новая сессия чата: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Ошибка при создании сессии чата: {e}")
            if self.session:
                self.session.rollback()
            return None
    
    def get_or_create_active_session(self, user_id: int) -> Optional[ChatSession]:
        """Получить активную сессию или создать новую"""
        try:
            if not self.session:
                logger.warning("⚠️ База данных не инициализирована")
                return None
                
            # Ищем активную сессию (последнюю созданную за последние 24 часа)
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            active_session = self.session.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= cutoff_time
            ).order_by(ChatSession.created_at.desc()).first()
            
            if active_session:
                logger.info(f"💬 Используем существующую сессию: {active_session.session_id}")
                return active_session
            else:
                # Создаем новую сессию
                return self.create_chat_session(user_id)
                
        except Exception as e:
            logger.error(f"Ошибка при получении активной сессии: {e}")
            return None
    
    def save_message(self, session_id: str, user_message: str, bot_response: str,
                    sources: list = None, complexity_level: str = "medium", processing_time: float = None) -> bool:
        """Сохранить сообщение в базу данных"""
        try:
            if not self.session:
                logger.warning("⚠️ База данных не инициализирована")
                return False
                
            sources_json = json.dumps(sources) if sources else None
            
            message = Message(
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                sources=sources_json,
                complexity_level=complexity_level,
                processing_time=processing_time
            )
            self.session.add(message)
            self.session.commit()
            
            logger.debug(f"💾 Сообщение сохранено в базу данных")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения: {e}")
            if self.session:
                self.session.rollback()
            return False
    
    def get_user_stats(self, telegram_id: str) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        try:
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return {}
            
            # Количество сообщений
            message_count = self.session.query(Message).join(
                ChatSession, Message.session_id == ChatSession.session_id
            ).filter(ChatSession.user_id == user.id).count()
            
            # Количество сессий
            session_count = self.session.query(ChatSession).filter(
                ChatSession.user_id == user.id
            ).count()
            
            return {
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "complexity_level": user.complexity_level,
                "message_count": message_count,
                "session_count": session_count,
                "created_at": user.created_at
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики пользователя: {e}")
            return {}
    
    def close(self):
        """Закрыть соединение с базой данных"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose() 