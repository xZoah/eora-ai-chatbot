#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI + Telegram бота в Railway
"""

import os
import asyncio
import threading
import uvicorn
from app.main import app
from app.bot.telegram_bot import EoraTelegramBot

def run_fastapi():
    """Запустить FastAPI сервер"""
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting FastAPI server on port {port}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )

def run_telegram_bot():
    """Запустить Telegram бота"""
    print("🤖 Starting Telegram bot...")
    try:
        bot = EoraTelegramBot()
        bot.run_bot()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

async def main():
    """Главная функция"""
    print(f"📦 Deployed version: {os.getenv('DEPLOYED_VERSION', 'unknown')}")
    print("🔄 Starting both FastAPI and Telegram bot...")
    
    # Запускаем FastAPI в отдельном потоке
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Ждем немного для запуска FastAPI
    await asyncio.sleep(2)
    
    # Запускаем Telegram бота в основном потоке
    run_telegram_bot()

if __name__ == "__main__":
    # Определяем режим запуска
    mode = os.getenv("RUN_MODE", "both")  # both, api, bot
    
    if mode == "api":
        # Только FastAPI
        run_fastapi()
    elif mode == "bot":
        # Только Telegram бот
        run_telegram_bot()
    else:
        # Оба сервиса
        asyncio.run(main()) 