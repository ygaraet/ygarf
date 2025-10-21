import requests
from bs4 import BeautifulSoup
from typing import List, Dict

from data.config import HABR_URL


def get_habr_articles() -> List[Dict]:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    url = HABR_URL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "ru,en;q=0.9",
        "Referer": "https://habr.com/",
        "Cache-Control": "no-cache",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    try:
        session = requests.Session()
        session.cookies.set("hl", "ru")
        logging.info(f"Загружаю страницу: {url}")
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        logging.info(f"Получен ответ: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Ошибка загрузки: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles: List[Dict] = []
    
    # Попробуем разные селекторы
    selectors = [
        'article.tm-articles-list__item',
        'article[data-test-id="article-card"]',
        'article',
        '.tm-articles-list__item',
        '[data-test-id="article-card"]'
    ]
    
    article_nodes = []
    for selector in selectors:
        article_nodes = soup.select(selector)
        if article_nodes:
            logging.info(f"Найдено {len(article_nodes)} статей с селектором: {selector}")
            break
    
    if not article_nodes:
        logging.warning("Статьи не найдены ни одним селектором")
        # Сохраним HTML для отладки
        with open('debug_habr.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logging.info("HTML сохранен в debug_habr.html")
        return []

    for i, article_tag in enumerate(article_nodes[:10]):  # Ограничим 10 статьями
        try:
            # Ищем заголовок разными способами
            title = ""
            link = ""
            
            # Способ 1: стандартный селектор
            title_link = article_tag.find('a', class_='tm-article-snippet__title-link')
            if title_link:
                title_span = title_link.find('span')
                title = (title_span.text if title_span else title_link.text).strip()
                link = 'https://habr.com' + (title_link.get('href') or '')
            else:
                # Способ 2: альтернативные селекторы
                h2 = article_tag.find('h2')
                if h2:
                    a = h2.find('a')
                    if a:
                        title = a.text.strip()
                        link = 'https://habr.com' + (a.get('href') or '')
                else:
                    # Способ 3: любой заголовок
                    h1 = article_tag.find('h1')
                    h3 = article_tag.find('h3')
                    header = h1 or h3
                    if header:
                        a = header.find('a')
                        if a:
                            title = a.text.strip()
                            link = 'https://habr.com' + (a.get('href') or '')
                        else:
                            title = header.text.strip()

            if not title:
                continue
                
            # Ищем изображение
            image_url = None
            img_selectors = [
                'img.tm-article-snippet__lead-image',
                'img[data-test-id="article-image"]',
                'img'
            ]
            for img_sel in img_selectors:
                img = article_tag.select_one(img_sel)
                if img and img.get('src'):
                    image_url = img.get('src')
                    break

            # Ищем описание
            description = ""
            desc_selectors = [
                '.article-formatted-body',
                '.tm-article-snippet__lead',
                '.tm-article-snippet',
                '[data-test-id="article-snippet"]'
            ]
            for desc_sel in desc_selectors:
                desc_elem = article_tag.select_one(desc_sel)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break

            articles.append({
                'title': title,
                'link': link,
                'image_url': image_url,
                'description': description or 'Описание отсутствует'
            })
            
            logging.info(f"Статья {i+1}: {title[:50]}...")
            
        except Exception as e:
            logging.error(f"Ошибка парсинга статьи {i}: {e}")
            continue

    logging.info(f"Всего найдено статей: {len(articles)}")
    return articles


def get_full_article_content(article_url: str) -> Dict:
    """Получить полное содержимое статьи"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "ru,en;q=0.9",
        "Referer": "https://habr.com/",
        "Cache-Control": "no-cache",
    }
    
    try:
        session = requests.Session()
        session.cookies.set("hl", "ru")
        logging.info(f"Загружаю полную статью: {article_url}")
        response = session.get(article_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем основной контент статьи
        content_selectors = [
            '.article-formatted-body',
            '.tm-article-body',
            '[data-test-id="article-content"]',
            '.post__text'
        ]
        
        content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(separator='\n', strip=True)
                break
        
        if not content:
            content = "Содержимое статьи не найдено"
        
        # Ищем дополнительные метаданные
        title_elem = soup.find('h1', class_='tm-title') or soup.find('h1')
        title = title_elem.text.strip() if title_elem else "Заголовок не найден"
        
        author_elem = soup.find('a', class_='tm-user-info__username') or soup.find('span', class_='tm-user-info__username')
        author = author_elem.text.strip() if author_elem else "Автор не найден"
        
        date_elem = soup.find('time') or soup.find('span', class_='tm-article-datetime')
        date = date_elem.text.strip() if date_elem else "Дата не найдена"
        
        # Ограничиваем размер контента для Telegram (4096 символов)
        if len(content) > 4000:
            content = content[:4000] + "\n\n... (полный текст читайте по ссылке)"
        
        return {
            'title': title,
            'author': author,
            'date': date,
            'content': content,
            'url': article_url
        }
        
    except requests.RequestException as e:
        logging.error(f"Ошибка загрузки статьи: {e}")
        return {
            'title': "Ошибка загрузки",
            'author': "Неизвестно",
            'date': "Неизвестно",
            'content': f"Не удалось загрузить статью: {e}",
            'url': article_url
        }
    except Exception as e:
        logging.error(f"Ошибка парсинга статьи: {e}")
        return {
            'title': "Ошибка парсинга",
            'author': "Неизвестно", 
            'date': "Неизвестно",
            'content': f"Ошибка при обработке статьи: {e}",
            'url': article_url
        }