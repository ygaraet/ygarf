import sys
import os
import aiohttp
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_status_code():
    """Тест проверки статус-кода Habr"""
    try:
        test_urls = [
            "https://habr.com/ru/articles/",  # Основная страница статей
            "https://habr.com/ru/",           # Главная страница
            "https://habr.com/",              # Международная версия
        ]
        
        print("=" * 50)
        print("ТЕСТ: Проверка доступности Habr")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            results = []
            
            for url in test_urls:
                try:
                    print(f"🔍 Проверяем: {url}")
                    async with session.get(url, timeout=10) as response:
                        status_code = response.status
                        
                        # Для Хабра допустимы 200, 301, 302 (редиректы)
                        is_success = status_code in [200, 301, 302]
                        status_emoji = "✅" if is_success else "❌"
                        
                        result = {
                            'url': url,
                            'status_code': status_code,
                            'success': is_success
                        }
                        
                        print(f"   {status_emoji} Статус-код: {status_code}")
                        
                        if status_code == 301 or status_code == 302:
                            print(f"   🔄 Редирект на: {response.headers.get('Location', 'неизвестно')}")
                        
                        results.append(result)
                        
                except aiohttp.ClientError as e:
                    print(f"   ❌ Ошибка подключения: {e}")
                    results.append({
                        'url': url,
                        'status_code': 'CONNECTION_ERROR',
                        'success': False
                    })
                except asyncio.TimeoutError:
                    print(f"   ⏰ Таймаут подключения")
                    results.append({
                        'url': url,
                        'status_code': 'TIMEOUT',
                        'success': False
                    })
        
        # Сводка результатов
        print("\n" + "=" * 30)
        print("ИТОГИ ПРОВЕРКИ HABR:")
        print("=" * 30)
        
        success_count = sum(1 for r in results if r['success'])
        
        for result in results:
            status_emoji = "✅" if result['success'] else "❌"
            print(f"{status_emoji} {result['url']} - {result['status_code']}")
        
        print(f"\n📊 Успешных подключений: {success_count}/{len(results)}")
        
        # Критерий прохождения: основная страница статей доступна
        main_success = any(r['success'] and '/articles/' in r['url'] for r in results)
        
        if main_success:
            print("✅ HABR ДОСТУПЕН: можно парсить статьи")
        else:
            print("❌ HABR НЕДОСТУПЕН: проблемы с подключением")
            
        return main_success
        
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_status_code())
    sys.exit(0 if result else 1)