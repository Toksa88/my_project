import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv(dotenv_path='tokenss.env')
# Получение токена бота из переменных окружения
bot_token = os.getenv('TG_TOKEN')
user_id = os.getenv('MY_TELEGRAM_ID')


