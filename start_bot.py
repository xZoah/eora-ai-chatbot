#!/usr/bin/env python3
"""
Скрипт для запуска только Telegram бота в Railway
"""

import os
import sys
from app.bot.telegram_bot import EoraTelegramBot

def run_telegram_bot():
    """Запустить только Telegram бота"""
    print("🤖 Starting EORA Telegram Bot")
    print(f"📦 Deployed version: {os.getenv('DEPLOYED_VERSION', 'unknown')}")
    
    try:
        # Создаем и запускаем бота
        bot = EoraTelegramBot()
        success = bot.run_bot()
        
        if success:
            print("✅ Bot started successfully")
        else:
            print("❌ Failed to start bot")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_telegram_bot() 