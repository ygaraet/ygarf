from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_article_keyboard(current_index, total_articles, article_url=None):
    buttons = []
    
    # Row 1: Navigation
    row1 = []
    if current_index > 0:
        row1.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="article_prev"))
    
    # Кнопка "Читать" теперь ведет на сайт статьи
    if article_url:
        row1.append(InlineKeyboardButton(text="Читать", url=article_url))
    else:
        row1.append(InlineKeyboardButton(text="Читать", callback_data="read_more"))

    if current_index < total_articles - 1:
        row1.append(InlineKeyboardButton(text="Вперед ➡️", callback_data="article_next"))
    
    buttons.append(row1)
    
    # Row 2: Full content button
    row2 = []
    row2.append(InlineKeyboardButton(text="📖 Полный текст", callback_data=f"full_content_{current_index}"))
    buttons.append(row2)

    return InlineKeyboardMarkup(inline_keyboard=buttons)