"""
Модуль для работы с Pinecone Vector Database
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pinecone import Pinecone, ServerlessSpec
from loguru import logger


@dataclass
class VectorMetadata:
    """Метаданные для вектора"""
    title: str
    description: str
    client: str
    technologies: List[str]
    url: str
    category: str
    content: str


class PineconeClient:
    """Клиент для работы с Pinecone"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "eora-cases")
        self.dimension = 1536  # Размерность для text-embedding-3-small
        self.metric = "cosine"
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY не найден в переменных окружения")
        
        # Инициализируем Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        
    def connect_to_index(self) -> bool:
        """Подключиться к существующему индексу"""
        try:
            if self.index_name not in self.pc.list_indexes().names():
                logger.error(f"Индекс {self.index_name} не найден")
                return False
            
            self.index = self.pc.Index(self.index_name)
            logger.success(f"✅ Подключились к индексу {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при подключении к индексу: {e}")
            return False
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """Загрузить векторы в Pinecone"""
        try:
            if not self.index:
                logger.error("Индекс не инициализирован")
                return False
            
            logger.info(f"Загружаем {len(vectors)} векторов в Pinecone...")
            
            # Разбиваем на батчи по 100 векторов
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Загружен батч {i//batch_size + 1}/{(len(vectors) + batch_size - 1)//batch_size}")
            
            logger.success(f"✅ Успешно загружено {len(vectors)} векторов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке векторов: {e}")
            return False
    
    def search_similar(self, query_vector: List[float], top_k: int = 5, 
                      filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск похожих векторов"""
        try:
            if not self.index:
                logger.error("Индекс не инициализирован")
                return []
            
            logger.info(f"Ищем {top_k} похожих векторов...")
            
            # Выполняем поиск
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            logger.success(f"Найдено {len(results['matches'])} результатов")
            return results['matches']
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return []
    
    def delete_vectors(self, ids: List[str]) -> bool:
        """Удалить векторы по ID"""
        try:
            if not self.index:
                logger.error("Индекс не инициализирован")
                return False
            
            logger.info(f"Удаляем {len(ids)} векторов...")
            self.index.delete(ids=ids)
            logger.success(f"Успешно удалено {len(ids)} векторов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении векторов: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Получить статистику индекса"""
        try:
            if not self.index:
                logger.error("Индекс не инициализирован")
                return {}
            
            stats = self.index.describe_index_stats()
            logger.info(f"Статистика индекса: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {}
    
    def create_vector_id(self, url: str) -> str:
        """Создать уникальный ID для вектора на основе URL"""
        # Убираем протокол и домен, оставляем путь
        path = url.replace("https://eora.ru", "").replace("http://eora.ru", "")
        # Заменяем слеши на подчеркивания
        vector_id = path.replace("/", "_").replace("-", "_")
        # Убираем лишние подчеркивания
        vector_id = "_".join(filter(None, vector_id.split("_")))
        return f"case_{vector_id}"
    
    def prepare_metadata(self, case_data: VectorMetadata) -> Dict[str, Any]:
        """Подготовить метаданные для вектора"""
        return {
            "title": case_data.title,
            "description": case_data.description,
            "client": case_data.client,
            "technologies": ",".join(case_data.technologies),
            "url": case_data.url,
            "category": case_data.category,
            "content_length": len(case_data.content)
        }


# Функция для тестирования подключения
def test_pinecone_connection():
    """Тестирование подключения к Pinecone"""
    try:
        client = PineconeClient()
        
        # Подключаемся к существующему индексу
        if client.connect_to_index():
            logger.success("✅ Подключение к Pinecone успешно")
            
            # Получаем статистику
            stats = client.get_index_stats()
            if stats:
                logger.info(f"📊 Статистика индекса: {stats}")
            
            return True
        else:
            logger.error("❌ Не удалось подключиться к индексу Pinecone")
            return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании Pinecone: {e}")
        return False


if __name__ == "__main__":
    # Тестируем подключение
    test_pinecone_connection() 