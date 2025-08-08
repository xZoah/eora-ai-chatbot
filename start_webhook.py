#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI + Telegram бота через webhook в Railway
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from app.main import app
from app.bot.telegram_bot import EoraTelegramBot

# Создаем глобальный экземпляр бота
telegram_bot = None

def initialize_telegram_bot():
    """Инициализировать Telegram бота"""
    global telegram_bot
    try:
        telegram_bot = EoraTelegramBot()
        # Инициализируем RAG и БД
        if telegram_bot.rag_manager:
            print("✅ RAG system initialized")
        if telegram_bot.database_service:
            print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return False

# Добавляем webhook endpoint к FastAPI
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Webhook endpoint для Telegram бота"""
    global telegram_bot
    
    if not telegram_bot:
        return {"error": "Bot not initialized"}
    
    try:
        # Получаем данные от Telegram
        data = await request.json()
        
        # Обрабатываем через бота
        await telegram_bot.handle_webhook_update(data)
        
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"error": str(e)}

@app.get("/webhook/telegram/setup")
async def setup_webhook():
    """Настроить webhook для Telegram бота"""
    global telegram_bot
    
    if not telegram_bot:
        return {"error": "Bot not initialized"}
    
    try:
        # Получаем URL приложения
        app_url = os.getenv("RAILWAY_STATIC_URL", "https://web-production-3cb0d.up.railway.app")
        webhook_url = f"{app_url}/webhook/telegram"
        
        # Настраиваем webhook
        success = telegram_bot.setup_webhook(webhook_url)
        
        if success:
            return {"status": "webhook_set", "url": webhook_url}
        else:
            return {"error": "Failed to set webhook"}
            
    except Exception as e:
        print(f"❌ Webhook setup error: {e}")
        return {"error": str(e)}

def main():
    """Главная функция"""
    print(f"📦 Deployed version: {os.getenv('DEPLOYED_VERSION', 'unknown')}")
    print("🔄 Starting FastAPI with Telegram webhook...")
    
    # Инициализируем бота
    if initialize_telegram_bot():
        print("✅ Telegram bot initialized successfully")
    else:
        print("⚠️ Telegram bot initialization failed, continuing with API only")
    
    # Запускаем FastAPI
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting FastAPI server on port {port}")
    
    uvicorn.run(
        "start_webhook:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )

if __name__ == "__main__":
    main() 