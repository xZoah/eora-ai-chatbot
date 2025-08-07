"""
Интеграционный модуль для управления векторной базой данных
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from .pinecone_client import PineconeClient
from .embedding_service import EmbeddingService, VectorProcessor


class VectorManager:
    """Менеджер для работы с векторной базой данных"""
    
    def __init__(self):
        self.pinecone_client = None
        self.embedding_service = None
        self.vector_processor = None
        
    def initialize_services(self) -> bool:
        """Инициализировать все сервисы"""
        try:
            # Инициализируем Pinecone
            logger.info("🔧 Инициализируем Pinecone...")
            self.pinecone_client = PineconeClient()
            
            # Подключаемся к индексу или создаем новый
            if not self.pinecone_client.connect_to_index():
                if not self.pinecone_client.create_index():
                    logger.error("Не удалось создать/подключиться к индексу Pinecone")
                    return False
            
            # Инициализируем сервис эмбеддингов
            logger.info("🔧 Инициализируем сервис эмбеддингов...")
            self.embedding_service = EmbeddingService()
            
            # Тестируем сервис эмбеддингов
            if not self.embedding_service.test_embedding_generation():
                logger.error("Сервис эмбеддингов не работает")
                return False
            
            # Создаем процессор векторов
            self.vector_processor = VectorProcessor(self.embedding_service)
            
            logger.success("✅ Все сервисы инициализированы успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации сервисов: {e}")
            return False
    
    def load_cases_from_json(self, filepath: str) -> List[Dict[str, Any]]:
        """Загрузить кейсы из JSON файла"""
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                logger.error(f"Файл {filepath} не найден")
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            logger.info(f"Загружено {len(cases)} кейсов из {filepath}")
            return cases
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке кейсов: {e}")
            return []
    
    async def enhance_cases_with_ai(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обогатить кейсы с помощью AI"""
        try:
            from app.llm.llm_service import LLMService
            llm_service = LLMService()
            
            enhanced_cases = []
            for i, case in enumerate(cases):
                logger.info(f"Обогащаем кейс {i+1}/{len(cases)}: {case.get('title', '')[:50]}...")
                
                # Если клиент не указан, попробуем извлечь его с помощью AI
                if case.get("client") == "Клиент не указан":
                    # Сначала попробуем извлечь из заголовка и описания
                    title = case.get('title', '').lower()
                    description = case.get('description', '').lower()
                    
                    # Список известных клиентов для поиска
                    known_clients = [
                        'сбер', 'sber', 'додо', 'dodo', 'магнит', 'avon', 'purina', 
                        'lamoda', 'kazanexpress', 'qiwi', 'столото', 'stoloto',
                        'goose gaming', 'sportrecs', 'ifarm', 'zeptolab'
                    ]
                    
                    found_client = None
                    for client in known_clients:
                        if client in title or client in description:
                            found_client = client
                            break
                    
                    if found_client:
                        # Улучшаем форматирование названий клиентов
                        if found_client in ['сбер', 'sber']:
                            case["client"] = "Сбер"
                        elif found_client in ['додо', 'dodo']:
                            case["client"] = "Додо Пицца"
                        elif found_client == 'магнит':
                            case["client"] = "Магнит"
                        elif found_client == 'avon':
                            case["client"] = "Avon"
                        elif found_client == 'purina':
                            case["client"] = "Purina"
                        elif found_client == 'lamoda':
                            case["client"] = "Lamoda"
                        elif found_client == 'kazanexpress':
                            case["client"] = "KazanExpress"
                        elif found_client == 'qiwi':
                            case["client"] = "QIWI"
                        elif found_client in ['столото', 'stoloto']:
                            case["client"] = "Столото"
                        elif found_client == 'goose gaming':
                            case["client"] = "Goose Gaming"
                        elif found_client == 'sportrecs':
                            case["client"] = "Sportrecs"
                        elif found_client == 'ifarm':
                            case["client"] = "iFarm"
                        elif found_client == 'zeptolab':
                            case["client"] = "ZeptoLab"
                        else:
                            case["client"] = found_client.title()
                        
                        logger.info(f"Извлечен клиент из текста: {case['client']}")
                    else:
                        # Если не нашли в тексте, попробуем AI
                        context = f"Заголовок: {case.get('title', '')}\nОписание: {case.get('description', '')}\nКонтент: {case.get('content', '')[:1000]}"
                        
                        prompt = f"""
                        Извлеки название клиента из следующего текста о проекте.
                        Если клиент не указан явно, попробуй найти упоминания компаний, брендов или заказчиков.
                        
                        {context}
                        
                        Верни только название клиента, без дополнительного текста.
                        Если клиент не найден, верни "Клиент не указан".
                        """
                        
                        try:
                            client = await llm_service.generate_text(prompt)
                            if client and client.strip() and client.strip() != "Клиент не указан":
                                case["client"] = client.strip()
                                logger.info(f"AI извлек клиента: {client.strip()}")
                        except Exception as e:
                            logger.warning(f"Не удалось извлечь клиента для кейса {i+1}: {e}")
                
                # Если категория слишком общая, попробуем улучшить
                if case.get("category") == "Общие кейсы":
                    context = f"Заголовок: {case.get('title', '')}\nОписание: {case.get('description', '')}"
                    
                    prompt = f"""
                    Определи более точную категорию для проекта на основе заголовка и описания.
                    
                    {context}
                    
                    Верни только название категории, без дополнительного текста.
                    """
                    
                    try:
                        category = await llm_service.generate_text(prompt)
                        if category and category.strip():
                            case["category"] = category.strip()
                            logger.info(f"AI улучшил категорию: {category.strip()}")
                    except Exception as e:
                        logger.warning(f"Не удалось улучшить категорию для кейса {i+1}: {e}")
                
                enhanced_cases.append(case)
            
            logger.success(f"✅ Обогащено {len(enhanced_cases)} кейсов с помощью AI")
            return enhanced_cases
            
        except Exception as e:
            logger.error(f"Ошибка при обогащении кейсов AI: {e}")
            return cases
    
    async def process_and_upload_cases(self, cases: List[Dict[str, Any]], 
                               batch_size: int = 10, use_ai_enhancement: bool = True) -> bool:
        """Обработать кейсы и загрузить в Pinecone"""
        try:
            if not self.vector_processor or not self.pinecone_client:
                logger.error("Сервисы не инициализированы")
                return False
            
            logger.info(f"🚀 Начинаем обработку {len(cases)} кейсов...")
            
            # Обогащаем кейсы с помощью AI (опционально)
            if use_ai_enhancement:
                logger.info("🤖 Обогащаем кейсы с помощью AI...")
                cases = await self.enhance_cases_with_ai(cases)
            
            # Обрабатываем кейсы батчами
            all_vectors = []
            for i in range(0, len(cases), batch_size):
                batch = cases[i:i + batch_size]
                logger.info(f"Обрабатываем батч {i//batch_size + 1}/{(len(cases) + batch_size - 1)//batch_size}")
                
                # Обрабатываем батч
                vectors = self.vector_processor.process_cases_batch(batch)
                all_vectors.extend(vectors)
                
                # Загружаем в Pinecone
                if vectors:
                    if not self.pinecone_client.upsert_vectors(vectors):
                        logger.error(f"Ошибка при загрузке батча {i//batch_size + 1}")
                        return False
                
                # Небольшая пауза между батчами
                if i + batch_size < len(cases):
                    asyncio.sleep(1)
            
            logger.success(f"✅ Успешно обработано и загружено {len(all_vectors)} векторов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обработке кейсов: {e}")
            return False
    
    def search_similar_cases(self, query: str, top_k: int = 5, 
                           filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск похожих кейсов"""
        try:
            if not self.embedding_service or not self.pinecone_client:
                logger.error("Сервисы не инициализированы")
                return []
            
            # Генерируем эмбеддинг для запроса
            query_embedding = self.embedding_service.generate_embedding(query)
            if not query_embedding:
                logger.error("Не удалось сгенерировать эмбеддинг для запроса")
                return []
            
            # Ищем похожие векторы
            results = self.pinecone_client.search_similar(
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
            logger.info(f"Найдено {len(results)} похожих кейсов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return []
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Получить статистику индекса"""
        try:
            if not self.pinecone_client:
                logger.error("Pinecone клиент не инициализирован")
                return {}
            
            stats = self.pinecone_client.get_index_stats()
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {}


async def main():
    """Основная функция для тестирования"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Менеджер векторной базы данных")
    parser.add_argument("--file", type=str, default="data/eora_cases_full.json", 
                       help="Путь к JSON файлу с кейсами")
    parser.add_argument("--test", action="store_true", help="Только тестирование")
    parser.add_argument("--search", type=str, help="Поиск по запросу")
    parser.add_argument("--no-ai", action="store_true", help="Отключить AI-обогащение")
    
    args = parser.parse_args()
    
    # Создаем менеджер
    manager = VectorManager()
    
    # Инициализируем сервисы
    if not manager.initialize_services():
        logger.error("❌ Не удалось инициализировать сервисы")
        return
    
    if args.test:
        # Только тестирование
        logger.info("🧪 Режим тестирования")
        stats = manager.get_index_statistics()
        if stats:
            logger.info(f"📊 Статистика индекса: {stats}")
        return
    
    if args.search:
        # Поиск
        logger.info(f"🔍 Поиск: {args.search}")
        results = manager.search_similar_cases(args.search, top_k=3)
        
        for i, result in enumerate(results, 1):
            logger.info(f"\n--- Результат {i} ---")
            logger.info(f"Заголовок: {result.get('metadata', {}).get('title', 'N/A')}")
            logger.info(f"Клиент: {result.get('metadata', {}).get('client', 'N/A')}")
            logger.info(f"URL: {result.get('metadata', {}).get('url', 'N/A')}")
            logger.info(f"Схожесть: {result.get('score', 0):.3f}")
        return
    
    # Полная обработка
    logger.info("🚀 Начинаем полную обработку...")
    
    # Загружаем кейсы
    cases = manager.load_cases_from_json(args.file)
    if not cases:
        logger.error("Не удалось загрузить кейсы")
        return
    
    # Обрабатываем и загружаем
    use_ai_enhancement = not args.no_ai
    if await manager.process_and_upload_cases(cases, use_ai_enhancement=use_ai_enhancement):
        logger.success("✅ Обработка завершена успешно!")
        
        # Показываем статистику
        stats = manager.get_index_statistics()
        if stats:
            logger.info(f"📊 Статистика индекса: {stats}")
    else:
        logger.error("❌ Ошибка при обработке")


if __name__ == "__main__":
    asyncio.run(main()) 