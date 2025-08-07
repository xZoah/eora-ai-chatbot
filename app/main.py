"""
Основной файл FastAPI приложения
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.routes import chat_router, health_router

# Создание FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Интеллектуальный чат-бот для консультаций клиентов EORA",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    logger.info("🚀 EORA Chat Bot запускается...")
    
    # Инициализация подключений к БД и кешу
    # await init_database()
    # await init_cache()
    
    logger.info("✅ EORA Chat Bot успешно запущен!")

@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("🛑 EORA Chat Bot останавливается...")
    
    # Закрытие подключений
    # await close_database()
    # await close_cache()
    
    logger.info("✅ EORA Chat Bot остановлен!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    ) 