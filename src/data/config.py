from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv('TOKEN')
HABR_URL = 'https://habr.com/ru/articles' # URL, который будет парситься.

# Настройки парсера
PARSER_TIMEOUT = int(getenv('PARSER_TIMEOUT')) # Таймаут (в секундах).
PARSER_MAX_ARTICLES = int(getenv('PARSER_MAX_ARTICLES')) # Максимальное количество статей для парсинга.