from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from bot.parser.habr_parser import get_habr_articles
from bot.keyboards.inline import get_article_keyboard
from bot.keyboards.reply import get_reply_keyboard
from bot.state import articles, current_article_index

router = Router()


def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    # Escape Telegram MarkdownV2 special characters
    specials = r"_ * [ ] ( ) ~ ` > # + - = | { } . !".split()
    escaped = text
    for ch in specials:
        escaped = escaped.replace(ch, f"\\{ch}")
    return escaped


def build_caption_md(title: str, description: str) -> str:
    safe_title = escape_markdown_v2(title)
    safe_desc = escape_markdown_v2(description)
    return f"*{safe_title}*\n\n{safe_desc}"


@router.message(CommandStart())
async def cmd_start(message: Message):
    global articles, current_article_index
    # Приветствие всегда
    await message.answer(
        "🤖 Добро пожаловать! Я показываю свежие статьи с Habr.\nОтправляю первую подходящую статью и клавиши навигации.")

    articles.clear()
    articles.extend(get_habr_articles())
    current_article_index = 0
    if articles:
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
        
        # Send reply keyboard
        await message.answer(
            reply_markup=get_reply_keyboard(
                has_prev=True,  # Всегда показываем кнопку "Назад"
                has_next=current_article_index < len(articles) - 1,
            ),
        )
    else:
        await message.answer("Не удалось найти статьи. Попробуйте позже или откройте Habr: https://habr.com/ru/articles/")


@router.message(F.text.in_(["⬅️ Назад", "Вперед ➡️"]))
async def reply_nav(message: Message):
    global current_article_index
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
    await message.answer(
        reply_markup=get_reply_keyboard(
            has_prev=True,  # Всегда показываем кнопку "Назад"
            has_next=current_article_index < len(articles) - 1,
        ),
    )
