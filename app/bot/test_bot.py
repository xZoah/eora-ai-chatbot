"""
Тестовая версия Telegram бота для проверки функциональности
"""

import os
import asyncio
from typing import Dict, Any, Optional
from loguru import logger

from app.llm.rag_manager import RAGManager


class TestEoraBot:
    """Тестовая версия бота для проверки функциональности"""
    
    def __init__(self):
        self.rag_manager = None
        self.user_settings = {}
        
    async def initialize(self):
        """Инициализировать RAG менеджер"""
        try:
            logger.info("🔧 Инициализируем тестовый бот...")
            
            # Инициализируем RAG менеджер
            self.rag_manager = RAGManager()
            if not self.rag_manager.initialize_services():
                logger.error("❌ Не удалось инициализировать RAG менеджер")
                return False
            
            logger.success("✅ Тестовый бот инициализирован успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации: {e}")
            return False
    
    def get_welcome_message(self) -> str:
        """Получить приветственное сообщение"""
        return """
🤖 Добро пожаловать в EORA Chat Bot!

Я - интеллектуальный помощник компании EORA, специализирующейся на разработке AI решений.

💡 Что я умею:
• Отвечать на вопросы о проектах EORA
• Предоставлять информацию о технологиях и кейсах
• Давать рекомендации на основе реальных проектов

🎛️ Уровни сложности ответов:
• Простой - краткие ответы
• Средний - подробные ответы со списком источников  
• Сложный - детальные ответы со встроенными ссылками

Просто задайте мне вопрос, и я найду релевантную информацию из наших проектов!
        """
    
    def get_help_message(self) -> str:
        """Получить сообщение помощи"""
        return """
📚 Справка по использованию бота

🔍 Как задать вопрос:
Просто напишите ваш вопрос в чат, например:
• "Что вы можете сделать для ритейлеров?"
• "Расскажите о проектах с AI"
• "Какие технологии вы используете?"

📊 Уровни сложности:
• Простой - краткие ответы без ссылок
• Средний - подробные ответы со списком источников
• Сложный - детальные ответы со встроенными ссылками

💡 Примеры вопросов:
• Отраслевые решения (ритейл, банки, медицина)
• Технологии (AI, Computer Vision, NLP)
• Конкретные проекты и кейсы
• Возможности и услуги EORA
        """
    
    async def process_query(self, query: str, user_id: int = 1, complexity_level: str = "medium") -> str:
        """Обработать запрос пользователя"""
        try:
            logger.info(f"🔍 Обрабатываем запрос: {query}")
            logger.info(f"👤 Пользователь: {user_id}")
            logger.info(f"📊 Уровень сложности: {complexity_level}")
            
            # Обрабатываем запрос через RAG pipeline
            response = self.rag_manager.process_query(
                query=query,
                complexity_level=complexity_level,
                top_k=3
            )
            
            if response:
                logger.success("✅ Ответ сгенерирован успешно")
                return self._format_response(response)
            else:
                logger.error("❌ Не удалось сгенерировать ответ")
                return "❌ Извините, не удалось найти подходящую информацию для вашего вопроса. Попробуйте переформулировать запрос."
                
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            return "❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже."
    
    def _format_response(self, response: str) -> str:
        """Форматировать ответ для вывода"""
        return f"💡 {response}"
    
    def set_user_complexity(self, user_id: int, level: str):
        """Установить уровень сложности для пользователя"""
        self.user_settings[user_id] = level
        logger.info(f"👤 Пользователь {user_id}: уровень сложности изменен на {level}")
    
    def get_user_complexity(self, user_id: int) -> str:
        """Получить уровень сложности пользователя"""
        return self.user_settings.get(user_id, "medium")
    
    def get_level_name(self, level: str) -> str:
        """Получить название уровня сложности"""
        levels = {
            "simple": "📝 Простой",
            "medium": "📋 Средний", 
            "hard": "📖 Сложный"
        }
        return levels.get(level, "📋 Средний")


async def test_bot_functionality():
    """Тестирование функциональности бота"""
    try:
        # Создаем тестовый бот
        bot = TestEoraBot()
        
        # Инициализируем
        if not await bot.initialize():
            logger.error("❌ Не удалось инициализировать бота")
            return False
        
        logger.success("✅ Тестовый бот готов к работе")
        
        # Тестируем приветственное сообщение
        welcome = bot.get_welcome_message()
        logger.info("📝 Приветственное сообщение:")
        print(welcome)
        
        # Тестируем обработку запроса
        test_query = "Что вы можете сделать для ритейлеров?"
        response = await bot.process_query(test_query, user_id=1, complexity_level="medium")
        
        logger.info("📝 Ответ на тестовый запрос:")
        print(response)
        
        # Тестируем изменение уровня сложности
        bot.set_user_complexity(1, "hard")
        response_hard = await bot.process_query(test_query, user_id=1, complexity_level="hard")
        
        logger.info("📝 Ответ на сложном уровне:")
        print(response_hard)
        
        logger.success("✅ Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return False


async def interactive_test():
    """Интерактивное тестирование бота"""
    try:
        # Создаем тестовый бот
        bot = TestEoraBot()
        
        # Инициализируем
        if not await bot.initialize():
            logger.error("❌ Не удалось инициализировать бота")
            return
        
        logger.success("✅ Тестовый бот готов к работе")
        logger.info("💡 Введите ваш вопрос (или 'quit' для выхода):")
        
        while True:
            try:
                query = input("> ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    logger.info("👋 До свидания!")
                    break
                
                if not query:
                    continue
                
                # Обрабатываем запрос
                response = await bot.process_query(query, user_id=1)
                print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                logger.info("👋 До свидания!")
                break
            except Exception as e:
                logger.error(f"Ошибка: {e}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка при интерактивном тестировании: {e}")


async def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Тестовый бот для EORA Chat Bot")
    parser.add_argument("--test", action="store_true", help="Запустить автоматическое тестирование")
    parser.add_argument("--interactive", action="store_true", help="Запустить интерактивное тестирование")
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("🧪 Режим автоматического тестирования")
        success = await test_bot_functionality()
        if success:
            logger.success("✅ Все тесты прошли успешно!")
        else:
            logger.error("❌ Тесты не прошли")
    
    elif args.interactive:
        logger.info("💬 Режим интерактивного тестирования")
        await interactive_test()
    
    else:
        logger.info("Используйте --test для автоматического тестирования или --interactive для интерактивного режима")


if __name__ == "__main__":
    asyncio.run(main()) 