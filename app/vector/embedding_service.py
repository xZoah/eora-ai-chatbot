"""
Сервис для генерации эмбеддингов с помощью OpenAI API
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import openai
from loguru import logger


class EmbeddingService:
    """Сервис для работы с эмбеддингами"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Настраиваем OpenAI
        openai.api_key = self.api_key
        self.model = "text-embedding-3-small"
        
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Генерировать эмбеддинг для текста"""
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("Пустой текст для генерации эмбеддинга")
                return None
            
            # Ограничиваем длину текста для API
            max_length = 8000  # Лимит для OpenAI
            if len(text) > max_length:
                text = text[:max_length]
                logger.info(f"Текст обрезан до {max_length} символов")
            
            # Генерируем эмбеддинг
            response = openai.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding
            
            logger.debug(f"Сгенерирован эмбеддинг размерности {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддинга: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Генерировать эмбеддинги для батча текстов"""
        embeddings = []
        
        for i, text in enumerate(texts):
            logger.info(f"Генерируем эмбеддинг {i+1}/{len(texts)}")
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
            
            # Небольшая задержка между запросами
            if i < len(texts) - 1:
                asyncio.sleep(0.1)
        
        return embeddings
    
    def prepare_text_for_embedding(self, title: str, description: str, 
                                 content: str, technologies: List[str]) -> str:
        """Подготовить текст для генерации эмбеддинга"""
        # Создаем структурированный текст
        text_parts = []
        
        if title:
            text_parts.append(f"Заголовок: {title}")
        
        if description:
            text_parts.append(f"Описание: {description}")
        
        if technologies:
            tech_text = ", ".join(technologies)
            text_parts.append(f"Технологии: {tech_text}")
        
        if content:
            # Берем первые 5000 символов контента
            content_preview = content[:5000]
            text_parts.append(f"Содержание: {content_preview}")
        
        return "\n\n".join(text_parts)
    
    def test_embedding_generation(self) -> bool:
        """Тестирование генерации эмбеддингов"""
        try:
            test_text = "Это тестовый текст для проверки генерации эмбеддингов"
            embedding = self.generate_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                logger.success(f"✅ Тест генерации эмбеддингов успешен. Размерность: {len(embedding)}")
                return True
            else:
                logger.error("❌ Не удалось сгенерировать эмбеддинг")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании: {e}")
            return False


class VectorProcessor:
    """Процессор для работы с векторами"""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
    
    def process_case_data(self, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обработать данные кейса и создать вектор"""
        try:
            # Подготавливаем текст для эмбеддинга
            text = self.embedding_service.prepare_text_for_embedding(
                title=case_data.get('title', ''),
                description=case_data.get('description', ''),
                content=case_data.get('content', ''),
                technologies=case_data.get('technologies', [])
            )
            
            # Генерируем эмбеддинг
            embedding = self.embedding_service.generate_embedding(text)
            if not embedding:
                logger.error(f"Не удалось сгенерировать эмбеддинг для кейса: {case_data.get('title', 'Unknown')}")
                return None
            
            # Создаем вектор с метаданными
            vector_data = {
                'id': f"case_{case_data.get('url', '').replace('/', '_').replace('-', '_')}",
                'values': embedding,
                'metadata': {
                    'title': case_data.get('title', ''),
                    'description': case_data.get('description', ''),
                    'client': case_data.get('client', ''),
                    'technologies': ','.join(case_data.get('technologies', [])),
                    'url': case_data.get('url', ''),
                    'category': case_data.get('category', ''),
                    'content_length': len(case_data.get('content', ''))
                }
            }
            
            return vector_data
            
        except Exception as e:
            logger.error(f"Ошибка при обработке кейса: {e}")
            return None
    
    def process_cases_batch(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработать батч кейсов"""
        vectors = []
        
        for i, case in enumerate(cases):
            logger.info(f"Обрабатываем кейс {i+1}/{len(cases)}: {case.get('title', 'Unknown')}")
            
            vector = self.process_case_data(case)
            if vector:
                vectors.append(vector)
            else:
                logger.warning(f"Пропускаем кейс {i+1}: не удалось обработать")
        
        logger.info(f"Успешно обработано {len(vectors)} из {len(cases)} кейсов")
        return vectors


def test_embedding_service():
    """Тестирование сервиса эмбеддингов"""
    try:
        # Создаем сервис
        embedding_service = EmbeddingService()
        
        # Тестируем генерацию
        if embedding_service.test_embedding_generation():
            logger.success("✅ Сервис эмбеддингов работает корректно")
            return True
        else:
            logger.error("❌ Сервис эмбеддингов не работает")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании сервиса эмбеддингов: {e}")
        return False


if __name__ == "__main__":
    # Тестируем сервис
    test_embedding_service() 