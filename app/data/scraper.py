"""
Парсер для сайта eora.ru
Извлекает информацию о кейсах и проектах компании
"""

import asyncio
import aiohttp
import time
import re
import unicodedata
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger
from dataclasses import dataclass


@dataclass
class CaseData:
    """Структура данных для кейса"""
    title: str
    description: str
    client: str
    technologies: List[str]
    url: str
    category: Optional[str] = None
    content: Optional[str] = None


class EoraScraper:
    """Парсер для сайта eora.ru"""
    
    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от Unicode-символов и лишних пробелов"""
        if not text:
            return ""
        
        # Удаляем невидимые Unicode-символы (включая U+200E)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Cf')
        
        # Удаляем другие проблемные символы
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)  # Zero-width characters
        
        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем лишние пробелы в начале и конце
        text = text.strip()
        
        return text
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Получить HTML страницы с retry логикой"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Загружаем страницу: {url} (попытка {attempt + 1})")
                
                async with self.session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.success(f"Успешно загружена страница: {url}")
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} для {url}")
                        
            except Exception as e:
                logger.error(f"Ошибка при загрузке {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                    
        logger.error(f"Не удалось загрузить {url} после {self.max_retries} попыток")
        return None
    
    def parse_case_page(self, html: str, url: str) -> Optional[CaseData]:
        """Парсинг страницы кейса"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Извлекаем заголовок
            title = self._extract_title(soup)
            
            # Извлекаем описание
            description = self._extract_description(soup)
            
            # Извлекаем клиента
            client = self._extract_client(soup)
            
            # Извлекаем технологии
            technologies = self._extract_technologies(soup)
            
            # Извлекаем категорию из URL
            category = self._extract_category_from_url(url)
            
            # Извлекаем основной контент
            content = self._extract_content(soup)
            
            return CaseData(
                title=title,
                description=description,
                client=client,
                technologies=technologies,
                url=url,
                category=category,
                content=content
            )
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечение заголовка кейса"""
        # Пробуем разные селекторы для заголовка
        selectors = [
            'h1',
            '.case-title',
            '.project-title',
            'h1.case-title',
            '.hero h1',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return "Без названия"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлечение описания кейса"""
        # Пробуем разные селекторы для описания
        selectors = [
            '.case-description',
            '.project-description',
            '.hero p',
            '.intro p',
            'meta[name="description"]',
            '.content p:first-of-type'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if selector == 'meta[name="description"]':
                    description = element.get('content', '')
                else:
                    description = element.get_text(strip=True)
                
                if description and len(description) > 20:
                    return description
        
        return "Описание не найдено"
    
    def _extract_client(self, soup: BeautifulSoup) -> str:
        """Извлечение названия клиента"""
        # Пробуем найти клиента в тексте
        text = soup.get_text().lower()
        
        # Список известных клиентов из технического задания
        known_clients = [
            'магнит', 'kazanexpress', 'lamoda', 'dodo pizza', 'purina',
            'avon', 's7', 'qiwi', 'intel', 'karcher', 'нейронет', 'skolkovo',
            'workeat', 'додо пицца', 'додо', 'goose gaming', 'химрар', 'chemrar',
            'skinclub', 'skin club', 'столото', 'stoloto'
        ]
        
        # Сначала ищем точные совпадения
        for client in known_clients:
            if client in text:
                # Улучшаем форматирование названий клиентов
                if client == 'dodo pizza' or client == 'додо пицца' or client == 'додо':
                    return "Додо Пицца"
                elif client == 'workeat':
                    return "WorkEat"
                elif client == 'goose gaming':
                    return "Goose Gaming"
                elif client == 'химрар' or client == 'chemrar':
                    return "Химрар"
                elif client == 'skinclub' or client == 'skin club':
                    return "SkinClub"
                elif client == 'столото' or client == 'stoloto':
                    return "Столото"
                else:
                    return client.title()
        
        # Ищем упоминания клиентов в контенте более гибко
        client_patterns = [
            r'клиент[:\s]+([^\.\n]+)',
            r'заказчик[:\s]+([^\.\n]+)',
            r'для\s+([^\.\n]+?)(?:\.|$)',
            r'проект\s+для\s+([^\.\n]+?)(?:\.|$)',
            r'кейс\s+для\s+([^\.\n]+?)(?:\.|$)'
        ]
        
        import re
        for pattern in client_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                client_name = matches[0].strip()
                # Очищаем название клиента
                client_name = re.sub(r'[«»""]', '', client_name)
                if len(client_name) > 2 and len(client_name) < 50:
                    return client_name.title()
        
        # Ищем упоминания в заголовках и описаниях
        title_text = soup.find('title')
        if title_text:
            title_lower = title_text.get_text().lower()
            for client in known_clients:
                if client in title_lower:
                    if client == 'dodo pizza' or client == 'додо пицца' or client == 'додо':
                        return "Додо Пицца"
                    elif client == 'workeat':
                        return "WorkEat"
                    elif client == 'goose gaming':
                        return "Goose Gaming"
                    elif client == 'химрар' or client == 'chemrar':
                        return "Химрар"
                    elif client == 'skinclub' or client == 'skin club':
                        return "SkinClub"
                    elif client == 'столото' or client == 'stoloto':
                        return "Столото"
                    else:
                        return client.title()
        
        return "Клиент не указан"
    
    def _extract_technologies(self, soup: BeautifulSoup) -> List[str]:
        """Извлечение используемых технологий"""
        technologies = []
        text = soup.get_text().lower()
        
        # Список технологий для поиска
        tech_keywords = [
            'python', 'javascript', 'react', 'vue', 'angular', 'node.js',
            'machine learning', 'ai', 'neural network', 'computer vision',
            'nlp', 'chatbot', 'api', 'docker', 'kubernetes', 'postgresql',
            'mongodb', 'redis', 'elasticsearch', 'tensorflow', 'pytorch',
            'openai', 'gpt', 'transformer', 'deep learning', 'ml'
        ]
        
        for tech in tech_keywords:
            if tech in text:
                technologies.append(tech.title())
        
        return list(set(technologies))  # Убираем дубликаты
    
    def _extract_category_from_url(self, url: str) -> str:
        """Извлечение категории из URL"""
        if '/cases/' in url:
            # Извлекаем категорию из URL
            parts = url.split('/cases/')
            if len(parts) > 1:
                category = parts[1].split('/')[0]
                # Улучшаем форматирование категорий
                category = category.replace('-', ' ').title()
                
                # Специальная обработка для известных категорий
                category_mapping = {
                    'workeat whatsapp bot': 'WorkEat WhatsApp Bot',
                    'dodo pizza robot analitik otzyvov': 'Додо Пицца - Робот-аналитик',
                    'dodo pizza bot dlya telefonii': 'Додо Пицца - Бот для телефонии',
                    'goosegaming algoritm dlya ocenki igrokov': 'Goose Gaming - Алгоритм оценки игроков',
                    'lamoda systema segmentacii i poiska po pohozhey odezhde': 'Lamoda - Система сегментации',
                    'zeptolab skazki pro amnyama dlya sberbox': 'ZeptoLab - Сказки для SberBox',
                    'assistenty dlya gorodov': 'Ассистенты для городов',
                    'navyki dlya golosovyh assistentov': 'Навыки для голосовых ассистентов',
                    'avtomatizaciya v promyshlennosti': 'Автоматизация в промышленности',
                    'kompyuternoe zrenie i ii': 'Компьютерное зрение и ИИ',
                    'razrabotka chat botov': 'Разработка чат-ботов',
                    'avtomatizaciya kontakt centrov': 'Автоматизация контакт-центров'
                }
                
                if category.lower() in category_mapping:
                    return category_mapping[category.lower()]
                
                return category
        
        return "Общие кейсы"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Извлечение основного контента страницы"""
        # Удаляем ненужные элементы
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Ищем основной контент
        content_selectors = [
            '.content',
            '.case-content',
            '.project-content',
            'main',
            'article',
            '.text-content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                return self._clean_text(content)
        
        # Если не нашли специальный контейнер, берем весь текст
        content = soup.get_text(strip=True)
        return self._clean_text(content)
    
    async def scrape_cases(self, urls: List[str]) -> List[CaseData]:
        """Парсинг всех кейсов"""
        cases = []
        
        for i, url in enumerate(urls):
            logger.info(f"Обрабатываем кейс {i+1}/{len(urls)}: {url}")
            
            # Загружаем страницу
            html = await self.fetch_page(url)
            if not html:
                continue
            
            # Парсим кейс
            case = self.parse_case_page(html, url)
            if case:
                cases.append(case)
                logger.success(f"Успешно обработан кейс: {case.title}")
            else:
                logger.warning(f"Не удалось обработать кейс: {url}")
            
            # Задержка между запросами
            if i < len(urls) - 1:  # Не ждем после последнего запроса
                await asyncio.sleep(self.delay)
        
        logger.info(f"Обработано {len(cases)} кейсов из {len(urls)}")
        return cases


# Список URL для парсинга из технического задания
EORA_CASES_URLS = [
    "https://eora.ru/cases/promyshlennaya-bezopasnost",
    "https://eora.ru/cases/lamoda-systema-segmentacii-i-poiska-po-pohozhey-odezhde",
    "https://eora.ru/cases/navyki-dlya-golosovyh-assistentov/karas-golosovoy-assistent",
    "https://eora.ru/cases/assistenty-dlya-gorodov",
    "https://eora.ru/cases/avtomatizaciya-v-promyshlennosti/chemrar-raspoznovanie-molekul",
    "https://eora.ru/cases/zeptolab-skazki-pro-amnyama-dlya-sberbox",
    "https://eora.ru/cases/goosegaming-algoritm-dlya-ocenki-igrokov",
    "https://eora.ru/cases/dodo-pizza-robot-analitik-otzyvov",
    "https://eora.ru/cases/ifarm-nejroset-dlya-ferm",
    "https://eora.ru/cases/zhivibezstraha-navyk-dlya-proverki-rodinok",
    "https://eora.ru/cases/sportrecs-nejroset-operator-sportivnyh-translyacij",
    "https://eora.ru/cases/avon-chat-bot-dlya-zhenshchin",
    "https://eora.ru/cases/navyki-dlya-golosovyh-assistentov/navyk-dlya-proverki-loterejnyh-biletov",
    "https://eora.ru/cases/computer-vision/iss-analiz-foto-avtomobilej",
    "https://eora.ru/cases/purina-master-bot",
    "https://eora.ru/cases/skinclub-algoritm-dlya-ocenki-veroyatnostej",
    "https://eora.ru/cases/skolkovo-chat-bot-dlya-startapov-i-investorov",
    "https://eora.ru/cases/purina-podbor-korma-dlya-sobaki",
    "https://eora.ru/cases/purina-navyk-viktorina",
    "https://eora.ru/cases/dodo-pizza-pilot-po-avtomatizacii-kontakt-centra",
    "https://eora.ru/cases/dodo-pizza-avtomatizaciya-kontakt-centra",
    "https://eora.ru/cases/icl-bot-sufler-dlya-kontakt-centra",
    "https://eora.ru/cases/s7-navyk-dlya-podbora-aviabiletov",
    "https://eora.ru/cases/workeat-whatsapp-bot",
    "https://eora.ru/cases/absolyut-strahovanie-navyk-dlya-raschyota-strahovki",
    "https://eora.ru/cases/kazanexpress-poisk-tovarov-po-foto",
    "https://eora.ru/cases/kazanexpress-sistema-rekomendacij-na-sajte",
    "https://eora.ru/cases/intels-proverka-logotipa-na-plagiat",
    "https://eora.ru/cases/karcher-viktorina-s-voprosami-pro-uborku",
    "https://eora.ru/cases/chat-boty/purina-friskies-chat-bot-na-sajte",
    "https://eora.ru/cases/nejroset-segmentaciya-video",
    "https://eora.ru/cases/chat-boty/essa-nejroset-dlya-generacii-rolikov",
    "https://eora.ru/cases/qiwi-poisk-anomalij",
    "https://eora.ru/cases/frisbi-nejroset-dlya-raspoznavaniya-pokazanij-schetchikov",
    "https://eora.ru/cases/skazki-dlya-gugl-assistenta",
    "https://eora.ru/cases/chat-boty/hr-bot-dlya-magnit-kotoriy-priglashaet-na-sobesedovanie"
]


async def main():
    """Основная функция для тестирования парсера"""
    logger.info("🚀 Запуск парсера EORA...")
    
    async with EoraScraper(delay=1.0) as scraper:
        # Парсим первые 3 кейса для тестирования
        test_urls = EORA_CASES_URLS[:3]
        cases = await scraper.scrape_cases(test_urls)
        
        # Выводим результаты
        for i, case in enumerate(cases, 1):
            logger.info(f"\n--- Кейс {i} ---")
            logger.info(f"Заголовок: {case.title}")
            logger.info(f"Клиент: {case.client}")
            logger.info(f"Технологии: {', '.join(case.technologies)}")
            logger.info(f"URL: {case.url}")
            logger.info(f"Описание: {case.description[:100]}...")
    
    logger.info("✅ Парсинг завершен!")


if __name__ == "__main__":
    asyncio.run(main()) 