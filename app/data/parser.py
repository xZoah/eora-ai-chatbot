"""
Модуль для сохранения и управления данными парсера
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from .scraper import EoraScraper, CaseData, EORA_CASES_URLS


class DataManager:
    """Менеджер для работы с данными парсера"""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def save_cases_to_json(self, cases: List[CaseData], filename: str = None) -> str:
        """Сохранить кейсы в JSON файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eora_cases_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Конвертируем CaseData в словари
        cases_data = []
        for case in cases:
            case_dict = {
                "title": case.title,
                "description": case.description,
                "client": case.client,
                "technologies": case.technologies,
                "url": case.url,
                "category": case.category,
                "content": case.content,
                "parsed_at": datetime.now().isoformat()
            }
            cases_data.append(case_dict)
        
        # Сохраняем в JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cases_data, f, ensure_ascii=False, indent=2)
        
        logger.success(f"Сохранено {len(cases)} кейсов в {filepath}")
        return str(filepath)
    
    def load_cases_from_json(self, filename: str) -> List[Dict[str, Any]]:
        """Загрузить кейсы из JSON файла"""
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            logger.error(f"Файл {filepath} не найден")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            cases_data = json.load(f)
        
        logger.info(f"Загружено {len(cases_data)} кейсов из {filepath}")
        return cases_data
    
    def get_statistics(self, cases: List[CaseData]) -> Dict[str, Any]:
        """Получить статистику по кейсам"""
        if not cases:
            return {}
        
        # Статистика по клиентам
        clients = {}
        for case in cases:
            client = case.client
            clients[client] = clients.get(client, 0) + 1
        
        # Статистика по технологиям
        technologies = {}
        for case in cases:
            for tech in case.technologies:
                technologies[tech] = technologies.get(tech, 0) + 1
        
        # Статистика по категориям
        categories = {}
        for case in cases:
            category = case.category
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_cases": len(cases),
            "clients": clients,
            "technologies": technologies,
            "categories": categories,
            "avg_content_length": sum(len(case.content or "") for case in cases) / len(cases)
        }


async def run_full_parsing(output_filename: str = None) -> str:
    """Запустить полный парсинг всех кейсов"""
    logger.info("🚀 Запуск полного парсинга EORA...")
    
    # Создаем менеджер данных
    data_manager = DataManager()
    
    # Парсим все кейсы
    async with EoraScraper(delay=1.0) as scraper:
        cases = await scraper.scrape_cases(EORA_CASES_URLS)
    
    if not cases:
        logger.error("Не удалось получить данные")
        return ""
    
    # Сохраняем в JSON
    filepath = data_manager.save_cases_to_json(cases, output_filename)
    
    # Выводим статистику
    stats = data_manager.get_statistics(cases)
    logger.info("\n📊 Статистика парсинга:")
    logger.info(f"Всего кейсов: {stats['total_cases']}")
    logger.info(f"Клиентов: {len(stats['clients'])}")
    logger.info(f"Технологий: {len(stats['technologies'])}")
    logger.info(f"Категорий: {len(stats['categories'])}")
    
    # Топ клиентов
    top_clients = sorted(stats['clients'].items(), key=lambda x: x[1], reverse=True)[:5]
    logger.info("\n🏆 Топ клиентов:")
    for client, count in top_clients:
        logger.info(f"  {client}: {count} кейсов")
    
    # Топ технологий
    top_tech = sorted(stats['technologies'].items(), key=lambda x: x[1], reverse=True)[:5]
    logger.info("\n🔧 Топ технологий:")
    for tech, count in top_tech:
        logger.info(f"  {tech}: {count} кейсов")
    
    return filepath


async def run_test_parsing(num_cases: int = 3) -> str:
    """Запустить тестовый парсинг нескольких кейсов"""
    logger.info(f"🧪 Запуск тестового парсинга ({num_cases} кейсов)...")
    
    # Создаем менеджер данных
    data_manager = DataManager()
    
    # Парсим тестовые кейсы
    test_urls = EORA_CASES_URLS[:num_cases]
    async with EoraScraper(delay=1.0) as scraper:
        cases = await scraper.scrape_cases(test_urls)
    
    if not cases:
        logger.error("Не удалось получить данные")
        return ""
    
    # Сохраняем в JSON
    filepath = data_manager.save_cases_to_json(cases, f"test_cases_{num_cases}.json")
    
    # Выводим результаты
    logger.info("\n📋 Результаты тестового парсинга:")
    for i, case in enumerate(cases, 1):
        logger.info(f"\n--- Кейс {i} ---")
        logger.info(f"Заголовок: {case.title}")
        logger.info(f"Клиент: {case.client}")
        logger.info(f"Технологии: {', '.join(case.technologies)}")
        logger.info(f"URL: {case.url}")
        logger.info(f"Описание: {case.description[:100]}...")
    
    return filepath


def validate_parsed_data(cases: List[CaseData]) -> Dict[str, List[str]]:
    """Валидация данных после парсинга"""
    issues = {
        "missing_title": [],
        "missing_description": [],
        "missing_client": [],
        "short_content": []
    }
    
    for i, case in enumerate(cases):
        # Проверяем заголовок
        if not case.title or case.title == "Без названия":
            issues["missing_title"].append(f"Кейс {i+1}: {case.url}")
        
        # Проверяем описание
        if not case.description or case.description == "Описание не найдено":
            issues["missing_description"].append(f"Кейс {i+1}: {case.url}")
        
        # Проверяем клиента
        if not case.client or case.client == "Клиент не указан":
            issues["missing_client"].append(f"Кейс {i+1}: {case.url}")
        
        # Проверяем длину контента
        if case.content and len(case.content) < 100:
            issues["short_content"].append(f"Кейс {i+1}: {case.url} ({len(case.content)} символов)")
    
    return issues


async def main():
    """Основная функция для запуска парсера"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Парсер кейсов EORA")
    parser.add_argument("--test", action="store_true", help="Запустить тестовый парсинг")
    parser.add_argument("--num-test", type=int, default=3, help="Количество кейсов для тестирования")
    parser.add_argument("--output", type=str, help="Имя выходного файла")
    
    args = parser.parse_args()
    
    if args.test:
        filepath = await run_test_parsing(args.num_test)
    else:
        filepath = await run_full_parsing(args.output)
    
    if filepath:
        logger.success(f"✅ Парсинг завершен! Файл сохранен: {filepath}")
    else:
        logger.error("❌ Парсинг не удался")


if __name__ == "__main__":
    asyncio.run(main()) 