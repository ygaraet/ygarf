import sys
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def get_habr_articles():
    """Парсим статьи с Habr"""
    url = "https://habr.com/ru/articles/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    articles = []
                    # Ищем статьи на странице
                    post_elements = soup.find_all('article', class_='tm-articles-list__item')[:10]  # Берем первые 10
                    
                    for post in post_elements:
                        # Заголовок
                        title_elem = post.find('h2', class_='tm-title') or post.find('h3') or post.find('h2')
                        title = title_elem.text.strip() if title_elem else 'Без заголовка'
                        
                        # Ссылка на статью
                        link_elem = title_elem.find('a') if title_elem else None
                        article_url = "https://habr.com" + link_elem.get('href') if link_elem else ''
                        
                        # Краткое описание
                        summary_elem = post.find('div', class_='article-formatted-body') or post.find('p')
                        summary = summary_elem.text.strip() if summary_elem else ''
                        
                        # Изображение (у Хабра не всегда есть превью)
                        image_elem = post.find('img')
                        image = image_elem.get('src') if image_elem else ''
                        
                        articles.append({
                            'title': title,
                            'image': image,
                            'summary': summary,
                            'url': article_url
                        })
                    
                    return articles
                else:
                    print(f"Ошибка: статус код {response.status}")
                    return []
                    
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return []

async def test_news_list():
    """Тест получения статей с Habr"""
    try:
        articles = await get_habr_articles()
        
        print("=" * 50)
        print("ТЕСТ: Получение статей с Habr")
        print("=" * 50)
        
        # Критерий прохождения: есть хотя бы 3 статьи
        assert len(articles) >= 3, f"Мало статей: {len(articles)} (нужно минимум 3)"
        assert isinstance(articles, list), "Результат должен быть списком"
        
        print(f"✅ УСПЕХ: Получено {len(articles)} статей")
        print("📊 Примеры статей:")
        
        for i, article in enumerate(articles[:3]):
            print(f"  {i+1}. {article['title'][:60]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_news_list())
    sys.exit(0 if result else 1)