from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_reply_keyboard(has_prev: bool, has_next: bool) -> ReplyKeyboardMarkup:
    buttons_row = []
    
    # Кнопка "Полный текст" всегда есть
    buttons_row.append(KeyboardButton(text="📖 Полный текст"))
    
    if has_prev:
        buttons_row.append(KeyboardButton(text="⬅️ Назад"))
    if has_next:
        buttons_row.append(KeyboardButton(text="Вперед ➡️"))
    
    return ReplyKeyboardMarkup(
        keyboard=[buttons_row],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие"
    )