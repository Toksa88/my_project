import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from google import genai
from google.genai import types

# 1. Завантаження ключів
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "tokenss.env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

TG_TOKEN = os.getenv("TG_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MY_TELEGRAM_ID = int(os.getenv("MY_TELEGRAM_ID"))

# 3. Ініціалізація
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-2.0-flash"
bot = Bot(token=TG_TOKEN)
dp = Dispatcher()


tools = [
    types.Tool(googleSearch=types.GoogleSearch(
    )),
]
generate_content_config = types.GenerateContentConfig(
    system_instruction="Балакаєш на українській",
    thinking_config=types.ThinkingConfig(
        thinking_level="LOW",
    ),
    tools=tools,
)


@dp.message(F.text, F.from_user.id == MY_TELEGRAM_ID)
async def handle_text_message(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status_msg = await message.reply("🤔 Gemini збирає думки до купи...")

    user_id = message.from_user.id
    try:
        # Відправляємо текст як абсолютно новий незалежний запит
        # і не забуваємо передати наш config з налаштуваннями!
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=message.text,
            config=generate_content_config
        )
        await status_msg.edit_text(response.text)

    except Exception as e:
        await status_msg.edit_text(f"Ой, щось пішло не так: {e}")


@dp.message(F.photo, F.from_user.id == MY_TELEGRAM_ID)
async def handle_homework_photo(message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status_msg = await message.reply("📸 Фото отримано! Gemini вже думає...")

    try:
        photo_id = message.photo[-1].file_id
        file_info = await bot.get_file(photo_id)
        downloaded_file = await bot.download_file(file_info.file_path)

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                "Ти крутий репетитор. Розв'яжи завдання на фото покроково українською мовою.",
                types.Part.from_bytes(
                    data=downloaded_file.read(), mime_type="image/jpeg")
            ]
        )
        await status_msg.edit_text(response.text)
    except Exception as e:
        await status_msg.edit_text(f"Помилка: {e}")


async def main():
    print(f"✅ Бот успішно запущений! Можеш кидати фото.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
