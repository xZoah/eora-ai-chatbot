"""
Сервис для работы с LLM API для генерации ответов
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import openai
from loguru import logger


class LLMService:
    """Сервис для работы с LLM API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Настраиваем OpenAI
        openai.api_key = self.api_key
        self.model = "gpt-4o-mini"  
        
    def generate_response(self, query: str, context: List[Dict[str, Any]], 
                         complexity_level: str = "medium") -> Optional[str]:
        """Генерировать ответ на основе запроса и контекста"""
        try:
            if not query or len(query.strip()) == 0:
                logger.warning("Пустой запрос для генерации ответа")
                return None
            
            # Подготавливаем промпт в зависимости от уровня сложности
            prompt = self._create_prompt(query, context, complexity_level)
            
            # Генерируем ответ
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Сгенерирован ответ длиной {len(answer)} символов")
            return answer
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Получить системный промпт"""
        return """Ты - помощник компании EORA, которая специализируется на разработке AI решений. 
Твоя задача - отвечать на вопросы потенциальных клиентов, используя информацию о реальных проектах компании.

ВАЖНЫЕ ПРАВИЛА:
1. Отвечай ТОЛЬКО на основе предоставленной информации о кейсах
2. НЕ ПРИДУМЫВАЙ проекты, которых нет в контексте
3. Будь конкретным и приводи примеры реальных проектов
4. Используй профессиональный, но дружелюбный тон
5. Если информации недостаточно, честно скажи об этом
6. Всегда упоминай конкретные технологии и результаты проектов
7. ИСПОЛЬЗУЙ Markdown ссылки [текст](url) для красивого форматирования
8. ИСПОЛЬЗУЙ **жирный текст** для выделения ключевых моментов
9. ИСПОЛЬЗУЙ *курсив* для заголовков и подзаголовков
10. Проверяй достоверность информации перед ответом
11. Включай реальные проекты: KazanExpress, S7 Airlines, Магнит, APM, ISS, iFarm, Сбер и другие
12. ФОКУСИРУЙСЯ на релевантности - выбирай только те проекты, которые точно соответствуют запросу
13. Если проект не соответствует запросу, НЕ включай его в ответ
14. Приоритет отдавай проектам с более высоким score релевантности
15. Используй ВСЕ предоставленные документы для формирования ответа (они уже отфильтрованы по релевантности)

Отвечай на русском языке."""
    
    def _create_prompt(self, query: str, context: List[Dict[str, Any]], 
                      complexity_level: str) -> str:
        """Создать промпт в зависимости от уровня сложности"""
        
        # Подготавливаем контекст
        context_text = self._format_context(context, complexity_level)
        
        base_prompt = f"""
Вопрос клиента: {query}

Информация о проектах EORA:
{context_text}

Пожалуйста, ответь на вопрос клиента, используя информацию о проектах выше.
"""
        
        if complexity_level == "simple":
            return base_prompt + "\nОтвечай кратко и по существу, без ссылок на источники."
        
        elif complexity_level == "medium":
            return base_prompt + "\nОтвечай подробно и обязательно укажи источники информации в конце ответа."
        
        elif complexity_level == "hard":
            return base_prompt + "\nОтвечай очень подробно, ОБЯЗАТЕЛЬНО вставляя ссылки на источники прямо в текст ответа. Каждый проект должен содержать ссылку в формате [название проекта](url)."
        
        else:
            return base_prompt + "\nОтвечай в среднем формате - подробно, но без излишней детализации."
    
    def _format_context(self, context: List[Dict[str, Any]], 
                       complexity_level: str) -> str:
         """Форматировать контекст для промпта с весами"""
         formatted_contexts = []
         
         for i, case in enumerate(context, 1):
             title = case.get('metadata', {}).get('title', 'Без названия')
             description = case.get('metadata', {}).get('description', '')
             client = case.get('metadata', {}).get('client', 'Клиент не указан')
             technologies = case.get('metadata', {}).get('technologies', '')
             url = case.get('metadata', {}).get('url', '')
             score = case.get('score', 0)
             
             # Добавляем вес релевантности
             case_text = f"""
 Проект {i} (релевантность: {score:.3f}): {title}
 Клиент: {client}
 Описание: {description}
 Технологии: {technologies}
 """
             
             if complexity_level in ["medium", "hard"]:
                 case_text += f"Источник: {url}\n"
             
             formatted_contexts.append(case_text)
         
         return "\n".join(formatted_contexts)
    
    def test_llm_connection(self) -> bool:
        """Тестирование подключения к LLM API"""
        try:
            test_prompt = "Привет! Расскажи кратко о компании EORA."
            response = self.generate_response(
                query=test_prompt,
                context=[{
                    'metadata': {
                        'title': 'Тестовый проект',
                        'description': 'EORA - компания, специализирующаяся на разработке AI решений',
                        'client': 'Тестовый клиент',
                        'technologies': 'AI, Machine Learning',
                        'url': 'https://eora.ru'
                    }
                }],
                complexity_level="simple"
            )
            
            if response and len(response) > 0:
                logger.success(f"✅ Тест LLM API успешен. Ответ: {response[:100]}...")
                return True
            else:
                logger.error("❌ Не удалось получить ответ от LLM API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании LLM API: {e}")
            return False
    
    async def generate_text(self, prompt: str) -> Optional[str]:
        """Генерировать текст на основе промпта (для AI-обогащения)"""
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - помощник для извлечения и анализа информации из текста. Отвечай кратко и точно."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при генерации текста: {e}")
            return None


class RAGPipeline:
    """Pipeline для RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, llm_service: LLMService, vector_service=None):
        self.llm_service = llm_service
        self.vector_service = vector_service
    
    def process_query(self, query: str, complexity_level: str = "medium", 
                     top_k: int = 3) -> Optional[str]:
        """Обработать запрос через RAG pipeline"""
        try:
            logger.info(f"🔍 Обрабатываем запрос: {query}")
            
            # 1. Поиск релевантного контекста
            if self.vector_service:
                context = self.vector_service.search_similar(query, top_k)
                logger.info(f"Найдено {len(context)} релевантных документов")
            else:
                logger.warning("Vector service не подключен, используем пустой контекст")
                context = []
            
            # 2. Генерация ответа
            response = self.llm_service.generate_response(
                query=query,
                context=context,
                complexity_level=complexity_level
            )
            
            if response:
                logger.success(f"✅ Ответ сгенерирован успешно")
                return response
            else:
                logger.error("❌ Не удалось сгенерировать ответ")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка в RAG pipeline: {e}")
            return None
    
    def test_pipeline(self) -> bool:
        """Тестирование RAG pipeline"""
        try:
            test_query = "Что вы можете сделать для ритейлеров?"
            response = self.process_query(test_query, "medium")
            
            if response:
                logger.success(f"✅ RAG pipeline работает. Ответ: {response[:200]}...")
                return True
            else:
                logger.error("❌ RAG pipeline не работает")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании RAG pipeline: {e}")
            return False


def test_llm_service():
    """Тестирование LLM сервиса"""
    try:
        # Создаем сервис
        llm_service = LLMService()
        
        # Тестируем подключение
        if llm_service.test_llm_connection():
            logger.success("✅ LLM сервис работает корректно")
            return True
        else:
            logger.error("❌ LLM сервис не работает")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании LLM сервиса: {e}")
        return False


if __name__ == "__main__":
    # Тестируем сервис
    test_llm_service() 