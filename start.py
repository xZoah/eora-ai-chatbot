#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI приложения в Railway
"""

import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Получаем порт из переменных окружения или используем 8000 по умолчанию
    port = int(os.getenv("PORT", 8000))
    
    # Запускаем FastAPI сервер
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    ) 