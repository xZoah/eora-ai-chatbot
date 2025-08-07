"""
Основное FastAPI приложение для EORA Chat Bot
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import time
import os

from app.api.routes import chat

# Создаем FastAPI приложение
app = FastAPI(
    title="EORA Chat Bot API",
    description="Интеллектуальный чат-бот для консультаций клиентов EORA",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования запросов"""
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"📥 {request.method} {request.url.path}")
    
    # Обрабатываем запрос
    response = await call_next(request)
    
    # Логируем время выполнения
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"❌ Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
        }
    )


@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    logger.info("🚀 Запуск EORA Chat Bot API...")
    
    # Проверяем необходимые переменные окружения
    required_env_vars = [
        "PINECONE_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
    
    logger.success("✅ EORA Chat Bot API запущен успешно!")


@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("🛑 Остановка EORA Chat Bot API...")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "EORA Chat Bot API",
        "version": "0.1.0",
        "status": "active",
        "docs": "/docs",
        "health": "/chat/health"
    }


@app.get("/health")
async def health_check():
    """Общий health check"""
    return {
        "status": "healthy",
        "service": "EORA Chat Bot API",
        "version": "0.1.0"
    }


# Подключаем роутеры
app.include_router(chat.router)


if __name__ == "__main__":
    import uvicorn
    
    # Запускаем сервер
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 