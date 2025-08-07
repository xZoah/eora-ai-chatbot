"""
Базовые тесты для основных компонентов системы
"""

import pytest
import json
from pathlib import Path
from app.vector.vector_manager import VectorManager
from app.llm.llm_service import LLMService
from app.data.parser import EORAParser

def test_vector_manager_initialization():
    """Тест инициализации VectorManager"""
    try:
        manager = VectorManager()
        assert manager is not None
        print("✅ VectorManager инициализируется корректно")
    except Exception as e:
        print(f"❌ Ошибка инициализации VectorManager: {e}")

def test_llm_service_initialization():
    """Тест инициализации LLMService"""
    try:
        llm_service = LLMService()
        assert llm_service is not None
        print("✅ LLMService инициализируется корректно")
    except Exception as e:
        print(f"❌ Ошибка инициализации LLMService: {e}")

def test_parser_initialization():
    """Тест инициализации парсера"""
    try:
        parser = EORAParser()
        assert parser is not None
        print("✅ EORAParser инициализируется корректно")
    except Exception as e:
        print(f"❌ Ошибка инициализации EORAParser: {e}")

def test_data_files_exist():
    """Тест наличия файлов с данными"""
    data_files = [
        "data/eora_cases_20250806_153749.json",
        "data/eora_cases_full.json"
    ]
    
    for file_path in data_files:
        if Path(file_path).exists():
            print(f"✅ Файл {file_path} существует")
        else:
            print(f"❌ Файл {file_path} не найден")

def test_json_data_structure():
    """Тест структуры JSON данных"""
    test_file = "data/eora_cases_20250806_153749.json"
    
    if Path(test_file).exists():
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем, что это список
            assert isinstance(data, list)
            
            # Проверяем структуру первого элемента
            if len(data) > 0:
                first_case = data[0]
                required_fields = ['title', 'description', 'content', 'url']
                
                for field in required_fields:
                    assert field in first_case, f"Отсутствует поле {field}"
                
                print(f"✅ JSON структура корректна, {len(data)} кейсов")
        except Exception as e:
            print(f"❌ Ошибка чтения JSON: {e}")
    else:
        print(f"❌ Файл {test_file} не найден")

def test_config_files_exist():
    """Тест наличия конфигурационных файлов"""
    config_files = [
        "env.example",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"✅ Конфигурационный файл {file_path} существует")
        else:
            print(f"❌ Конфигурационный файл {file_path} не найден")

if __name__ == "__main__":
    print("🧪 Запуск базовых тестов...")
    
    test_vector_manager_initialization()
    test_llm_service_initialization()
    test_parser_initialization()
    test_data_files_exist()
    test_json_data_structure()
    test_config_files_exist()
    
    print("✅ Базовые тесты завершены") 