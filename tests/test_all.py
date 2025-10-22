import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ")
    print("=" * 60)
    
    tests = [
        ("test_news_list.py", "Получение новостей"),
        ("test_validation.py", "Валидация полей"), 
        ("test_status_code.py", "Проверка статус-кодов")
    ]
    
    results = []
    
    for test_file, test_name in tests:
        print(f"\n🎯 Запуск теста: {test_name}")
        print("-" * 40)
        
        try:
            # Импортируем и запускаем каждый тест
            if test_file == "test_news_list.py":
                from test_news_list import test_news_list
                result = await test_news_list()
            elif test_file == "test_validation.py":
                from test_validation import test_validation
                result = await test_validation()
            elif test_file == "test_status_code.py":
                from test_status_code import test_status_code
                result = await test_status_code()
            else:
                result = False
                
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ Ошибка при запуске теста {test_file}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ТЕСТАМ")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("🎉 ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
        return True
    else:
        print("💥 НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)