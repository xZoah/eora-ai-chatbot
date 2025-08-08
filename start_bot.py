#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота в Railway
"""

import os
import sys
from app.bot.telegram_bot import EoraTelegramBot

if __name__ == "__main__":
    # Получаем информацию о деплое
    print(f"🤖 Starting EORA Telegram Bot")
    print(f"📦 Deployed version: {os.getenv('DEPLOYED_VERSION', 'unknown')}")
    
    try:
        # Создаем и запускаем бота
        bot = EoraTelegramBot()
        bot.run_bot()
        
    except KeyboardInterrupt:
        print("👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1) 