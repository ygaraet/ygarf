from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from bot.handlers.user_handlers import build_caption_md, escape_markdown_v2, split_message
from bot.keyboards.inline import get_article_keyboard
from bot.state import articles, current_article_index, clear_user_messages, add_user_message
from bot.parser.habr_parser import get_full_article_content

router = Router()

@router.callback_query(F.data.startswith("article_"))
async def paginate_articles(callback: CallbackQuery, bot: Bot):
    global current_article_index
    
    # Удаляем предыдущие сообщения с полным текстом при смене статьи
    await clear_user_messages(callback.from_user.id, bot)
    
    action = callback.data.split("_")[1]

    if action == "next":
        current_article_index += 1
    elif action == "prev":
        current_article_index -= 1
    
    if 0 <= current_article_index < len(articles):
        article = articles[current_article_index]
        caption = build_caption_md(article['title'], article['description'])

        has_photo_message = bool(callback.message.photo)
        target_has_image = bool(article.get('image_url'))

        try:
            if has_photo_message:
                if target_has_image:
                    media = InputMediaPhoto(media=article['image_url'], caption=caption, parse_mode="MarkdownV2")
                    await callback.message.edit_media(
                        media=media,
                        reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
                    )
                else:
                    # Оставляем текущее фото, меняем только подпись
                    await callback.message.edit_caption(
                        caption=caption,
                        parse_mode="MarkdownV2",
                        reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
                    )
            else:
                if target_has_image:
                    # Нельзя превратить текст в фото через edit; отправим новое фото и удалим старое сообщение
                    msg = await callback.message.answer_photo(
                        photo=article['image_url'],
                        caption=caption,
                        parse_mode="MarkdownV2",
                        reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
                    )
                    try:
                        await callback.message.delete()
                    except TelegramBadRequest:
                        pass
                else:
                    await callback.message.edit_text(
                        text=caption,
                        parse_mode="MarkdownV2",
                        reply_markup=get_article_keyboard(current_article_index, len(articles), article['link'])
                    )
        except TelegramBadRequest as e:
            await callback.answer(f"Ошибка обновления: {e}", show_alert=True)

    await callback.answer()

@router.callback_query(F.data.startswith("full_content_"))
async def show_full_content(callback: CallbackQuery, bot: Bot):
    """Показать полное содержимое статьи"""
    try:
        # Удаляем предыдущие сообщения с полным текстом
        await clear_user_messages(callback.from_user.id, bot)
        
        article_index = int(callback.data.split("_")[2])
        
        if 0 <= article_index < len(articles):
            article = articles[article_index]
            article_url = article['link']
            
            # Показываем загрузку
            await callback.answer("Загружаю полный текст статьи...", show_alert=False)
            
            # СИНХРОННЫЙ вызов - убрать await!
            full_content = get_full_article_content(article_url)
            
            if not full_content:
                await callback.answer("Не удалось загрузить статью", show_alert=True)
                return
            
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
                msg = await callback.message.answer(
                    message_text,
                    parse_mode="MarkdownV2",
                    disable_web_page_preview=True
                )
                sent_messages.append(msg.message_id)
            else:
                # Если контент длинный - разбиваем на части
                # Отправляем заголовок отдельно
                header_msg = await callback.message.answer(
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
                    
                    msg = await callback.message.answer(
                        part,
                        parse_mode="MarkdownV2",
                        disable_web_page_preview=True
                    )
                    sent_messages.append(msg.message_id)
            
            # Сохраняем ID отправленных сообщений
            for msg_id in sent_messages:
                add_user_message(callback.from_user.id, msg_id)
            
        else:
            await callback.answer("Статья не найдена", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"Ошибка загрузки: {str(e)}", show_alert=True)