"""
API эндпоинты для чат-бота
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger

from app.llm.rag_manager import RAGManager

router = APIRouter(prefix="/chat", tags=["chat"])

# Глобальный RAG менеджер
rag_manager = None


class ChatRequest(BaseModel):
    """Модель запроса для чата"""
    message: str = Field(..., description="Сообщение пользователя", min_length=1, max_length=1000)
    complexity_level: str = Field(default="medium", description="Уровень сложности ответа", 
                                pattern="^(simple|medium|hard)$")
    user_id: Optional[str] = Field(default=None, description="ID пользователя")


class ChatResponse(BaseModel):
    """Модель ответа чата"""
    response: str = Field(..., description="Ответ бота")
    complexity_level: str = Field(..., description="Использованный уровень сложности")
    sources: Optional[List[str]] = Field(default=None, description="Источники информации")
    processing_time: float = Field(..., description="Время обработки в секундах")


class HealthResponse(BaseModel):
    """Модель ответа для health check"""
    status: str = Field(..., description="Статус сервиса")
    rag_manager_ready: bool = Field(..., description="Готовность RAG менеджера")
    vector_db_ready: bool = Field(..., description="Готовность векторной БД")
    llm_ready: bool = Field(..., description="Готовность LLM")


async def get_rag_manager() -> RAGManager:
    """Получить RAG менеджер"""
    global rag_manager
    if rag_manager is None:
        try:
            rag_manager = RAGManager()
            if not rag_manager.initialize_services():
                raise HTTPException(status_code=503, detail="RAG сервисы недоступны")
        except Exception as e:
            logger.error(f"Ошибка инициализации RAG менеджера: {e}")
            raise HTTPException(status_code=503, detail="Ошибка инициализации сервисов")
    
    return rag_manager


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    rag_manager: RAGManager = Depends(get_rag_manager)
):
    """Основной эндпоинт для чата"""
    import time
    
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Получен запрос: {request.message[:50]}...")
        logger.info(f"👤 Пользователь: {request.user_id}")
        logger.info(f"📊 Уровень сложности: {request.complexity_level}")
        
        # Обрабатываем запрос через RAG pipeline
        response = rag_manager.process_query(
            query=request.message,
            complexity_level=request.complexity_level,
            top_k=3
        )
        
        processing_time = time.time() - start_time
        
        if response:
            logger.success(f"✅ Ответ сгенерирован за {processing_time:.2f}с")
            
            # Извлекаем источники из ответа (если есть)
            sources = extract_sources_from_response(response)
            
            return ChatResponse(
                response=response,
                complexity_level=request.complexity_level,
                sources=sources,
                processing_time=processing_time
            )
        else:
            logger.error("❌ Не удалось сгенерировать ответ")
            raise HTTPException(
                status_code=500, 
                detail="Не удалось найти подходящую информацию для вашего вопроса"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса"""
    try:
        # Проверяем RAG менеджер
        rag_manager = RAGManager()
        rag_ready = rag_manager.initialize_services()
        
        # Проверяем компоненты
        vector_db_ready = rag_manager.pinecone_client is not None
        llm_ready = rag_manager.llm_service is not None
        
        status = "healthy" if rag_ready else "unhealthy"
        
        return HealthResponse(
            status=status,
            rag_manager_ready=rag_ready,
            vector_db_ready=vector_db_ready,
            llm_ready=llm_ready
        )
        
    except Exception as e:
        logger.error(f"Ошибка при health check: {e}")
        return HealthResponse(
            status="unhealthy",
            rag_manager_ready=False,
            vector_db_ready=False,
            llm_ready=False
        )


@router.get("/test")
async def test_endpoint():
    """Тестовый эндпоинт"""
    return {
        "message": "EORA Chat Bot API работает!",
        "version": "0.1.0",
        "status": "active"
    }


def extract_sources_from_response(response: str) -> List[str]:
    """Извлечь источники из ответа"""
    import re
    
    # Ищем ссылки в формате [текст](ссылка)
    sources = []
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, response)
    
    for title, url in matches:
        sources.append(f"{title}: {url}")
    
    return sources if sources else None 