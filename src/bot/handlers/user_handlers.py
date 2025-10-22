from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart

from bot.parser.habr_parser import get_habr_articles, get_full_article_content
from bot.keyboards.inline import get_article_keyboard
from bot.keyboards.reply import get_reply_keyboard
from bot.state import articles, current_article_index, clear_user_messages, add_user_message

router = Router()

def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    # Экранируем ВСЕ специальные символы для MarkdownV2
    specials = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    escaped = text
    for ch in specials:
        escaped = escaped.replace(ch, f'\\{ch}')
    return escaped

def build_caption_md(title: str, description: str) -> str:
    safe_title = escape_markdown_v2(title)
    safe_desc = escape_markdown_v2(description)
    return f"*{safe_title}*\n\n{safe_desc}"

def split_message(text: str, max_length: int = 4000) -> list:
    """Разбивает длинное сообщение на части"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        # Ищем точку разрыва по предложению
        split_pos = text.rfind('.', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        
        parts.append(text[:split_pos + 1])
        text = text[split_pos + 1:].lstrip()
    
    return parts

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    global articles, current_article_index
    
    # Удаляем предыдущие сообщения с полным текстом
    await clear_user_messages(message.from_user.id, bot)
    
    await message.answer(
        "🤖 Добро пожаловать! Я показываю свежие статьи с Habr.\nОтправляю первую подходящую статью и клавиши навигации.")

    articles.clear()
    articles.extend(get_habr_articles())
    current_article_index = 0
    if articles:
        article = articles[current_article_index]
        caption = build_caption_md(article['title'], article['description'])
        if article['image_url']:
            msg = await message.answer_photo(
                photo=article['image_url'],
                caption=caption,
                parse_mode="MarkdownV2",
                reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
            )
        else:
            msg = await message.answer(
                caption,
                parse_mode="MarkdownV2",
                reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
            )
        
        # Send reply keyboard
        await message.answer(
            "Используйте кнопки для навигации:",
            reply_markup=get_reply_keyboard(
                has_prev=True,
                has_next=current_article_index < len(articles) - 1,
            ),
        )
    else:
        await message.answer("Не удалось найти статьи. Попробуйте позже или откройте Habr: https://habr.com/ru/articles/")

@router.message(F.text.in_(["⬅️ Назад", "Вперед ➡️"]))
async def reply_nav(message: Message, bot: Bot):
    global current_article_index
    
    # Удаляем предыдущие сообщения с полным текстом при смене статьи
    await clear_user_messages(message.from_user.id, bot)
    
    if not articles:
        await message.answer("Нет загруженных статей. Отправьте /start")
        return
    
    if message.text == "⬅️ Назад":
        if current_article_index > 0:
            current_article_index -= 1
        else:
            await message.answer("Вы уже на первой статье")
            return
    elif message.text == "Вперед ➡️":
        if current_article_index < len(articles) - 1:
            current_article_index += 1
        else:
            await message.answer("Вы уже на последней статье")
            return

    article = articles[current_article_index]
    caption = build_caption_md(article['title'], article['description'])
    if article['image_url']:
        await message.answer_photo(
            photo=article['image_url'],
            caption=caption,
            parse_mode="MarkdownV2",
            reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
        )
    else:
        await message.answer(
            caption,
            parse_mode="MarkdownV2",
            reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
        )

@router.message(F.text == "📖 Полный текст")
async def show_full_text(message: Message, bot: Bot):
    """Обработчик кнопки 'Полный текст'"""
    global current_article_index
    
    # Удаляем предыдущие сообщения с полным текстом
    await clear_user_messages(message.from_user.id, bot)
    
    print(f"🔴 DEBUG: Кнопка 'Полный текст' нажата!")
    print(f"🔴 DEBUG: current_article_index = {current_article_index}")
    print(f"🔴 DEBUG: Всего статей = {len(articles)}")
    
    if not articles:
        await message.answer("Нет загруженных статей. Отправьте /start")
        return
    
    if current_article_index < 0 or current_article_index >= len(articles):
        await message.answer("Ошибка: текущая статья не найдена")
        return
    
    article = articles[current_article_index]
    article_url = article['link']
    
    print(f"🔴 DEBUG: Статья URL = {article_url}")
    
    # Показываем уведомление о загрузке
    loading_msg = await message.answer("🔄 Загружаю полный текст статьи...")
    
    try:
        print(f"🔴 DEBUG: Вызываю get_full_article_content...")
        full_content = get_full_article_content(article_url)
        print(f"🔴 DEBUG: get_full_article_content вернул: {bool(full_content)}")
        
        if not full_content:
            await loading_msg.edit_text("❌ Не удалось загрузить статью")
            return
        
        print(f"🔴 DEBUG: Заголовок: {full_content['title']}")
        print(f"🔴 DEBUG: Контент длина: {len(full_content['content'])}")
        
        # Экранируем ВСЕ тексты для MarkdownV2
        safe_title = escape_markdown_v2(full_content['title'])
        safe_author = escape_markdown_v2(full_content['author'])
        safe_date = escape_markdown_v2(full_content['date'])
        safe_content = escape_markdown_v2(full_content['content'])
        
        # Формируем основное сообщение
        header_text = f"📖 *{safe_title}*\n\n👤 Автор: {safe_author}\n📅 Дата: {safe_date}\n\n"
        footer_text = f"\n\n🔗 [Читать на Habr]({article_url})"
        
        # Вычисляем доступное место для контента
        available_space = 4096 - len(header_text) - len(footer_text) - 100  # Запас
        
        sent_messages = []
        
        if len(safe_content) <= available_space:
            # Если контент помещается в одно сообщение
            message_text = header_text + safe_content + footer_text
            await loading_msg.delete()
            msg = await message.answer(
                message_text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )
            sent_messages.append(msg.message_id)
        else:
            # Если контент длинный - разбиваем на части
            await loading_msg.edit_text("📖 Загружаю статью (это может занять несколько сообщений)...")
            
            # Отправляем заголовок отдельно
            header_msg = await message.answer(
                header_text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )
            sent_messages.append(header_msg.message_id)
            
            # Разбиваем контент на части
            content_parts = split_message(safe_content, 4000)
            
            # Отправляем части контента
            for i, part in enumerate(content_parts, 1):
                if i == len(content_parts):
                    # В последней части добавляем ссылку
                    part += footer_text
                
                msg = await message.answer(
                    part,
                    parse_mode="MarkdownV2",
                    disable_web_page_preview=True
                )
                sent_messages.append(msg.message_id)
            
            await loading_msg.delete()
        
        # Сохраняем ID отправленных сообщений
        for msg_id in sent_messages:
            add_user_message(message.from_user.id, msg_id)
        
        print(f"🔴 DEBUG: Сообщение отправлено успешно! Сохранено {len(sent_messages)} сообщений")
        
    except Exception as e:
        print(f"🔴 DEBUG: Ошибка: {str(e)}")
        await loading_msg.edit_text(f"❌ Ошибка при загрузке статьи: {str(e)}")