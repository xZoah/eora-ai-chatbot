"""
Интегрированный RAG менеджер для объединения векторного поиска и LLM
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from app.vector.embedding_service import EmbeddingService
from app.vector.pinecone_client import PineconeClient
from app.llm.llm_service import LLMService, RAGPipeline


class RAGManager:
    """Интегрированный менеджер для RAG pipeline"""
    
    def __init__(self):
        self.embedding_service = None
        self.pinecone_client = None
        self.llm_service = None
        self.rag_pipeline = None
        
    def initialize_services(self) -> bool:
        """Инициализировать все сервисы"""
        try:
            logger.info("🔧 Инициализируем RAG сервисы...")
            
            # Инициализируем сервис эмбеддингов
            logger.info("🔧 Инициализируем сервис эмбеддингов...")
            self.embedding_service = EmbeddingService()
            if not self.embedding_service.test_embedding_generation():
                logger.error("❌ Не удалось инициализировать сервис эмбеддингов")
                return False
            
            # Инициализируем Pinecone клиент
            logger.info("🔧 Инициализируем Pinecone...")
            self.pinecone_client = PineconeClient()
            if not self.pinecone_client.connect_to_index():
                logger.error("❌ Не удалось подключиться к Pinecone")
                return False
            
            # Инициализируем LLM сервис
            logger.info("🔧 Инициализируем LLM сервис...")
            self.llm_service = LLMService()
            if not self.llm_service.test_llm_connection():
                logger.error("❌ Не удалось инициализировать LLM сервис")
                return False
            
            # Создаем RAG pipeline
            self.rag_pipeline = RAGPipeline(
                llm_service=self.llm_service,
                vector_service=self.pinecone_client
            )
            
            logger.success("✅ Все RAG сервисы инициализированы успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации сервисов: {e}")
            return False
    
    def process_query(self, query: str, complexity_level: str = "medium", 
                     top_k: int = 5) -> Optional[str]:
        """Обработать запрос через полный RAG pipeline"""
        try:
            if not self.rag_pipeline:
                logger.error("RAG pipeline не инициализирован")
                return None
            
            logger.info(f"🔍 Обрабатываем запрос: {query}")
            logger.info(f"📊 Уровень сложности: {complexity_level}")
            
            # Генерируем эмбеддинг для запроса
            query_embedding = self.embedding_service.generate_embedding(query)
            if not query_embedding:
                logger.error("Не удалось сгенерировать эмбеддинг для запроса")
                return None
            
            # Ищем похожие документы
            similar_docs = self.pinecone_client.search_similar(query_embedding, top_k)
            logger.info(f"Найдено {len(similar_docs)} релевантных документов")
            
            # Фильтруем документы по релевантности (порог 0.35)
            filtered_docs = [doc for doc in similar_docs if doc.get('score', 0) > 0.35]
            logger.info(f"После фильтрации по score > 0.35 осталось {len(filtered_docs)} документов")
            
            # Если после фильтрации документов нет, используем топ-2 с наивысшим score
            if len(filtered_docs) == 0:
                filtered_docs = sorted(similar_docs, key=lambda x: x.get('score', 0), reverse=True)[:2]
                logger.info(f"Нет документов с score > 0.35, используем топ-2: {len(filtered_docs)} документов")
            
            # Логируем найденные документы для отладки
            for i, doc in enumerate(filtered_docs, 1):
                metadata = doc.get('metadata', {})
                title = metadata.get('title', 'Без названия')
                client = metadata.get('client', 'Клиент не указан')
                score = doc.get('score', 0)
                logger.debug(f"📄 Документ {i}: {title} (клиент: {client}, релевантность: {score:.3f})")
            
            # Используем отфильтрованные документы
            similar_docs = filtered_docs
            
            # Генерируем ответ
            response = self.llm_service.generate_response(
                query=query,
                context=similar_docs,
                complexity_level=complexity_level
            )
            
            if response:
                logger.success("✅ Ответ сгенерирован успешно")
                return response
            else:
                logger.error("❌ Не удалось сгенерировать ответ")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка в RAG pipeline: {e}")
            return None
    
    def test_full_pipeline(self) -> bool:
        """Тестирование полного RAG pipeline"""
        try:
            test_query = "Что вы можете сделать для ритейлеров?"
            response = self.process_query(test_query, "medium")
            
            if response:
                logger.success(f"✅ Полный RAG pipeline работает!")
                logger.info(f"📝 Ответ: {response}")
                return True
            else:
                logger.error("❌ RAG pipeline не работает")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании RAG pipeline: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Получить статистику индекса"""
        if self.pinecone_client:
            return self.pinecone_client.get_index_stats()
        return {}


def test_rag_manager():
    """Тестирование RAG менеджера"""
    try:
        # Создаем менеджер
        rag_manager = RAGManager()
        
        # Инициализируем сервисы
        if rag_manager.initialize_services():
            logger.success("✅ RAG менеджер инициализирован успешно")
            
            # Тестируем полный pipeline
            if rag_manager.test_full_pipeline():
                logger.success("✅ Полный RAG pipeline работает корректно")
                return True
            else:
                logger.error("❌ RAG pipeline не работает")
                return False
        else:
            logger.error("❌ Не удалось инициализировать RAG менеджер")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании RAG менеджера: {e}")
        return False


async def main():
    """Основная функция для тестирования"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Manager для EORA Chat Bot")
    parser.add_argument("--test", action="store_true", help="Запустить тестирование")
    parser.add_argument("--query", type=str, help="Запрос для обработки")
    parser.add_argument("--complexity", type=str, default="medium", 
                       choices=["simple", "medium", "hard"], 
                       help="Уровень сложности ответа")
    parser.add_argument("--top-k", type=int, default=3, help="Количество похожих документов")
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("🧪 Режим тестирования")
        success = test_rag_manager()
        if success:
            logger.success("✅ Все тесты прошли успешно!")
        else:
            logger.error("❌ Тесты не прошли")
    
    elif args.query:
        logger.info(f"🔍 Обрабатываем запрос: {args.query}")
        rag_manager = RAGManager()
        
        if rag_manager.initialize_services():
            response = rag_manager.process_query(
                query=args.query,
                complexity_level=args.complexity,
                top_k=args.top_k
            )
            
            if response:
                logger.success("✅ Ответ сгенерирован:")
                print("\n" + "="*50)
                print(response)
                print("="*50)
            else:
                logger.error("❌ Не удалось сгенерировать ответ")
        else:
            logger.error("❌ Не удалось инициализировать сервисы")
    
    else:
        logger.info("Используйте --test для тестирования или --query для обработки запроса")


if __name__ == "__main__":
    asyncio.run(main()) 