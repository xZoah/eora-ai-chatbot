"""
Health check endpoints
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
@router.get("")
async def health_check() -> Dict[str, Any]:
    """Проверка состояния API"""
    try:
        return {
            "status": "healthy",
            "message": "EORA Chatbot API работает",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья API: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Проверка готовности сервиса"""
    try:
        # Здесь можно добавить проверки подключений к БД, Redis и т.д.
        return {
            "status": "ready",
            "message": "Сервис готов к работе",
            "services": {
                "api": "healthy",
                "vector_db": "healthy"  # Можно добавить реальную проверку
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при проверке готовности: {e}")
        raise HTTPException(status_code=503, detail="Сервис не готов") 