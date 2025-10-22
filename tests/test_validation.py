import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_news_list import get_habr_articles

async def test_validation():
    """Тест валидации статей с Habr"""
    try:
        articles = await get_habr_articles()
        
        print("=" * 50)
        print("ТЕСТ: Валидация статей Habr")
        print("=" * 50)
        
        assert len(articles) > 0, "Нет статей для проверки"
        
        validation_results = []
        habr_specific_checks = []
        
        for i, article in enumerate(articles):
            errors = []
            warnings = []
            
            # ОБЯЗАТЕЛЬНЫЕ проверки
            if not article.get('title'):
                errors.append("отсутствует заголовок")
            elif len(article['title'].strip()) == 0:
                errors.append("пустой заголовок")
            
            # У Хабра не всегда есть изображения в списке статей - это НЕ ошибка
            if article.get('image') and not article['image'].startswith(('http://', 'https://')):
                warnings.append("невалидная ссылка на изображение")
            
            # Краткое содержание
            if not article.get('summary'):
                warnings.append("отсутствует краткое содержание")  # У Хабра может не быть в списке
            elif len(article['summary'].strip()) < 5:  # Минимум 5 символов для Хабра
                warnings.append("очень короткое содержание")
            
            # Хабра-специфичные проверки
            if not article.get('url') or 'habr.com' not in article['url']:
                warnings.append("некорректная ссылка на статью")
            
            status = "✅ ВАЛИДНА" if not errors else f"❌ ОШИБКИ: {', '.join(errors)}"
            if warnings:
                status += f" | ⚠️ Предупреждения: {', '.join(warnings)}"
            
            validation_results.append((i, article.get('title', 'Без заголовка')[:50], status))
            
            # Собираем специфичные данные для анализа
            habr_specific_checks.append({
                'has_title': bool(article.get('title')),
                'has_image': bool(article.get('image')),
                'has_summary': bool(article.get('summary') and len(article['summary']) > 10),
                'has_valid_url': bool(article.get('url') and 'habr.com' in article['url'])
            })
        
        # Анализ данных по Хабрам
        total = len(habr_specific_checks)
        titles_count = sum(1 for x in habr_specific_checks if x['has_title'])
        images_count = sum(1 for x in habr_specific_checks if x['has_image'])
        summaries_count = sum(1 for x in habr_specific_checks if x['has_summary'])
        urls_count = sum(1 for x in habr_specific_checks if x['has_valid_url'])
        
        print(f"📊 Статистика по {total} статьям Habr:")
        print(f"  📝 Заголовки: {titles_count}/{total} ({titles_count/total*100:.1f}%)")
        print(f"  🖼️ Изображения: {images_count}/{total} ({images_count/total*100:.1f}%)")
        print(f"  📄 Описания: {summaries_count}/{total} ({summaries_count/total*100:.1f}%)")
        print(f"  🔗 Ссылки: {urls_count}/{total} ({urls_count/total*100:.1f}%)")
        
        # Критерий прохождения для Хабра:
        # - Есть статьи
        # - Большинство имеют заголовки и валидные ссылки
        success = (len(articles) >= 3 and 
                  titles_count/total >= 0.8 and  # 80% имеют заголовки
                  urls_count/total >= 0.9)       # 90% имеют валидные ссылки
        
        if success:
            print(f"\n✅ ТЕСТ ПРОЙДЕН: Статьи Habr соответствуют ожиданиям")
        else:
            print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: Проблемы с качеством данных")
            
        return success
        
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_validation())
    sys.exit(0 if result else 1)