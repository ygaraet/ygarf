from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from bot.handlers.user_handlers import build_caption_md
from bot.keyboards.inline import get_article_keyboard
from bot.state import articles, current_article_index
from bot.parser.habr_parser import get_full_article_content

router = Router()

@router.callback_query(F.data.startswith("article_"))
async def paginate_articles(callback: CallbackQuery):
    global current_article_index
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
async def show_full_content(callback: CallbackQuery):
    """Показать полное содержимое статьи"""
    try:
        article_index = int(callback.data.split("_")[2])
        
        if 0 <= article_index < len(articles):
            article = articles[article_index]
            article_url = article['link']
            
            # Показываем загрузку
            await callback.answer("Загружаю полный текст статьи...")
            
            # Получаем полное содержимое
            full_content = get_full_article_content(article_url)
            
            # Формируем сообщение
            message_text = f"📖 *{full_content['title']}*\n\n"
            message_text += f"👤 Автор: {full_content['author']}\n"
            message_text += f"📅 Дата: {full_content['date']}\n\n"
            message_text += f"{full_content['content']}\n\n"
            message_text += f"🔗 [Читать на Habr]({article_url})"
            
            # Отправляем сообщение
            await callback.message.answer(
                message_text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )
            
        else:
            await callback.answer("Статья не найдена", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"Ошибка загрузки: {e}", show_alert=True)
    
    await callback.answer()

# Обработчик read_more больше не нужен, так как кнопка "Читать" теперь ведет на сайт