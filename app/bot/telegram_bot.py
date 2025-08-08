"""
Telegram бот для EORA Chat Bot
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from loguru import logger
from dotenv import load_dotenv

from app.llm.rag_manager import RAGManager
from app.core.database_service import DatabaseService

# Загружаем переменные окружения из .env файла
load_dotenv()


class EoraTelegramBot:
    """Telegram бот для EORA Chat Bot"""

    def __init__(self):
        self.rag_manager = None
        self.database_service = None
        self.user_settings = {}
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

    async def initialize(self):
        """Инициализировать RAG менеджер и базу данных"""
        try:
            logger.info("🔧 Инициализируем Telegram бот...")

            # Инициализируем RAG менеджер
            self.rag_manager = RAGManager()
            if not self.rag_manager.initialize_services():
                logger.error("❌ Не удалось инициализировать RAG менеджер")
                return False

            # Инициализируем базу данных
            self.database_service = DatabaseService()
            if not self.database_service.initialize():
                logger.warning("⚠️ Не удалось инициализировать базу данных, продолжаем без неё")

            logger.success("✅ Telegram бот инициализирован успешно")
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

📊 Команды:
• /stats - показать вашу статистику

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

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        welcome_message = self.get_welcome_message()
        
        # Устанавливаем уровень сложности по умолчанию как "hard"
        self.user_settings[user_id] = "hard"
        
        # Сохраняем пользователя в базу данных
        if self.database_service:
            db_user = self.database_service.get_or_create_user(
                telegram_id=str(user_id),
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            if db_user:
                # Обновляем уровень сложности из базы данных
                self.user_settings[user_id] = db_user.complexity_level
        
        keyboard = [
            [InlineKeyboardButton("📋 Справка", callback_data="help")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = self.get_help_message()
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_message, reply_markup=reply_markup)

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        user_id = update.effective_user.id
        current_level = self.user_settings.get(user_id, "hard")
        
        message = f"⚙️ Настройки\n\nТекущий уровень сложности: {self.get_level_name(current_level)}"
        
        keyboard = [
            [InlineKeyboardButton("📝 Простой", callback_data="level_simple")],
            [InlineKeyboardButton("📋 Средний", callback_data="level_medium")],
            [InlineKeyboardButton("📖 Сложный", callback_data="level_hard")],
            [InlineKeyboardButton("🔙 Назад", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats - показать статистику пользователя"""
        user_id = update.effective_user.id
        
        if not self.database_service:
            await update.message.reply_text("❌ База данных не подключена")
            return
        
        try:
            stats = self.database_service.get_user_stats(str(user_id))
            
            if stats:
                message = f"📊 **Ваша статистика:**\n\n"
                message += f"• Сообщений: {stats.get('message_count', 0)}\n"
                message += f"• Сессий чата: {stats.get('session_count', 0)}\n"
                message += f"• Уровень сложности: {self.get_level_name(stats.get('complexity_level', 'medium'))}\n"
                message += f"• Дата регистрации: {stats.get('created_at', 'Неизвестно')}\n"
                
                await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ Статистика не найдена")
                
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            await update.message.reply_text("❌ Ошибка при получении статистики")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        if not message_text or len(message_text.strip()) == 0:
            return
        
        # Получаем уровень сложности для пользователя
        complexity_level = self.user_settings.get(user_id, "hard")
        
        logger.info(f"🔍 Обрабатываем сообщение от пользователя {user_id}: {message_text}")
        logger.info(f"📊 Уровень сложности: {complexity_level}")
        
        # Отправляем сообщение о том, что обрабатываем запрос
        processing_message = await update.message.reply_text("🤔 Обрабатываю ваш запрос...")
        
        try:
            # Обрабатываем запрос через RAG pipeline
            response = self.rag_manager.process_query(
                query=message_text,
                complexity_level=complexity_level,
                top_k=5
            )
            
            if response:
                # Форматируем ответ для Telegram
                formatted_response = self._format_response_for_telegram(response)
                await update.message.reply_text(formatted_response, parse_mode='HTML')
                logger.success(f"✅ Ответ отправлен пользователю {user_id}")
                
                # Сохраняем сообщение в базу данных
                if self.database_service:
                    # Получаем или создаем пользователя
                    db_user = self.database_service.get_or_create_user(
                        telegram_id=str(user_id),
                        username=update.effective_user.username,
                        first_name=update.effective_user.first_name,
                        last_name=update.effective_user.last_name
                    )
                    
                    if db_user:
                        # Получаем активную сессию или создаем новую
                        session = self.database_service.get_or_create_active_session(db_user.id)
                        if session:
                            # Сохраняем сообщение
                            self.database_service.save_message(
                                session_id=session.session_id,
                                user_message=message_text,
                                bot_response=response,
                                complexity_level=complexity_level
                            )
            else:
                await update.message.reply_text("❌ Извините, не удалось найти подходящую информацию для вашего вопроса. Попробуйте переформулировать запрос.")
                logger.error(f"❌ Не удалось сгенерировать ответ для пользователя {user_id}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        
        finally:
            # Удаляем сообщение о обработке
            try:
                await processing_message.delete()
            except:
                pass

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        await query.answer()
        
        if query.data == "start":
            welcome_message = self.get_welcome_message()
            keyboard = [
                [InlineKeyboardButton("📋 Справка", callback_data="help")],
                [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(welcome_message, reply_markup=reply_markup)
            
        elif query.data == "help":
            help_message = self.get_help_message()
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(help_message, reply_markup=reply_markup)
            
        elif query.data == "settings":
            current_level = self.user_settings.get(user_id, "hard")
            message = f"⚙️ Настройки\n\nТекущий уровень сложности: {self.get_level_name(current_level)}"
            
            keyboard = [
                [InlineKeyboardButton("📝 Простой", callback_data="level_simple")],
                [InlineKeyboardButton("📋 Средний", callback_data="level_medium")],
                [InlineKeyboardButton("📖 Сложный", callback_data="level_hard")],
                [InlineKeyboardButton("🔙 Назад", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            
        elif query.data.startswith("level_"):
            level = query.data.replace("level_", "")
            self.user_settings[user_id] = level
            level_name = self.get_level_name(level)
            
            # Обновляем уровень сложности в базе данных
            if self.database_service:
                self.database_service.update_user_complexity(str(user_id), level)
            
            message = f"✅ Уровень сложности изменен на: {level_name}"
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
            
            logger.info(f"👤 Пользователь {user_id}: уровень сложности изменен на {level}")

    def _format_response_for_telegram(self, response: str) -> str:
        """Форматировать ответ для Telegram"""
        import re
        
        # Обрабатываем Markdown ссылки [текст](url) -> HTML ссылки
        markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        def replace_markdown_link(match):
            link_text = match.group(1)
            url = match.group(2)
            return f'<a href="{url}">{link_text}</a>'
        
        # Заменяем Markdown ссылки на HTML ссылки
        formatted_response = re.sub(markdown_link_pattern, replace_markdown_link, response)
        
        # Обрабатываем **жирный текст** -> <b>жирный текст</b>
        bold_pattern = r'\*\*([^*]+)\*\*'
        
        def replace_bold(match):
            text = match.group(1)
            return f'<b>{text}</b>'
        
        formatted_response = re.sub(bold_pattern, replace_bold, formatted_response)
        
        # Обрабатываем *курсивный текст* -> <i>курсивный текст</i>
        italic_pattern = r'\*([^*]+)\*'
        
        def replace_italic(match):
            text = match.group(1)
            return f'<i>{text}</i>'
        
        formatted_response = re.sub(italic_pattern, replace_italic, formatted_response)
        
        # Обрабатываем ### заголовки -> <b>заголовки</b>
        header_pattern = r'###\s*([^\n]+)'
        
        def replace_header(match):
            text = match.group(1)
            return f'<b>{text}</b>'
        
        formatted_response = re.sub(header_pattern, replace_header, formatted_response)
        
        # Обрабатываем обычные URL (если они не в ссылках)
        url_pattern = r'(?<!<a href=")https?://[^\s]+(?!">)'
        
        def replace_url(match):
            url = match.group(0)
            return f'<a href="{url}">{url}</a>'
        
        formatted_response = re.sub(url_pattern, replace_url, formatted_response)
        
        # Добавляем эмодзи в начало
        return f"💡 {formatted_response}"

    def get_level_name(self, level: str) -> str:
        """Получить название уровня сложности"""
        levels = {
            "simple": "📝 Простой",
            "medium": "📋 Средний", 
            "hard": "📖 Сложный"
        }
        return levels.get(level, "📋 Средний")

    async def setup_webhook(self, webhook_url: str) -> bool:
        """Настроить webhook для бота"""
        try:
            from telegram import Bot
            
            bot = Bot(token=self.bot_token)
            result = await bot.set_webhook(url=webhook_url)
            
            if result:
                logger.success(f"✅ Webhook установлен: {webhook_url}")
                return True
            else:
                logger.error("❌ Не удалось установить webhook")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке webhook: {e}")
            return False

    async def handle_webhook_update(self, update_data: dict):
        """Обработать webhook update от Telegram"""
        try:
            from telegram import Update, Bot
            from telegram.ext import ContextTypes
            
            # Создаем Bot объект для обработки
            bot = Bot(token=self.bot_token)
            
            # Создаем Update объект из данных
            update = Update.de_json(update_data, bot)
            
            # Создаем контекст
            context = ContextTypes.DEFAULT_TYPE()
            context.bot = bot
            
            # Обрабатываем сообщение
            if update.message:
                await self.handle_message(update, context)
            elif update.callback_query:
                await self.handle_callback(update, context)
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке webhook: {e}")

    def run_bot(self):
        """Запустить бота (polling метод - для локальной разработки)"""
        try:
            # Инициализируем RAG менеджер
            if not self.rag_manager:
                self.rag_manager = RAGManager()
                if not self.rag_manager.initialize_services():
                    logger.error("❌ Не удалось инициализировать RAG менеджер")
                    return False

            # Инициализируем базу данных (опционально)
            if not self.database_service:
                try:
                    self.database_service = DatabaseService()
                    if not self.database_service.initialize():
                        logger.warning("⚠️ Не удалось инициализировать базу данных, продолжаем без неё")
                except Exception as e:
                    logger.warning(f"⚠️ База данных недоступна: {e}")

            # Создаем приложение
            self.application = Application.builder().token(self.bot_token).build()

            # Добавляем обработчики
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("settings", self.settings_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))

            logger.success("✅ Telegram бот готов к работе")
            logger.info("🤖 Бот запущен. Нажмите Ctrl+C для остановки.")

            # Запускаем бота с обработкой ошибок
            try:
                # Используем polling с дополнительными параметрами для Railway
                self.application.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                    close_loop=False,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30
                )
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка при запуске polling: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            return False


def main():
    """Основная функция"""
    try:
        # Создаем и запускаем бота
        bot = EoraTelegramBot()
        bot.run_bot()
        
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main() 