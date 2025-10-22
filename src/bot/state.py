# Глобальное состояние бота
articles = []
current_article_index = 0

# Храним ID сообщений с полным текстом для каждого пользователя
user_full_text_messages = {}

def get_user_messages(user_id: int):
    """Получить список сообщений с полным текстом для пользователя"""
    return user_full_text_messages.get(user_id, [])

def add_user_message(user_id: int, message_id: int):
    """Добавить ID сообщения для пользователя"""
    if user_id not in user_full_text_messages:
        user_full_text_messages[user_id] = []
    user_full_text_messages[user_id].append(message_id)

async def clear_user_messages(user_id: int, bot=None):
    """Удалить все сообщения с полным текстом для пользователя"""
    if user_id in user_full_text_messages and user_full_text_messages[user_id]:
        if bot:
            # Асинхронно удаляем сообщения
            for msg_id in user_full_text_messages[user_id]:
                try:
                    await bot.delete_message(user_id, msg_id)
                except Exception as e:
                    print(f"⚠️ Не удалось удалить сообщение {msg_id}: {e}")
        # Очищаем список сообщений пользователя
        user_full_text_messages[user_id] = []