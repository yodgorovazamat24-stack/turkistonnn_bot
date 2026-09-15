import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# Bot tokeni va kanal ID raqami
TOKEN = "8596519118:AAHYFVvax9dpJJy8s8LXAc_ZnBGnQdILMUY"
CHANNEL_ID = -1004452847162

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🎬 Assalomu alaykum! Kino botimizga xush kelibsiz.\n\n"
        "Kerakli kinoning kodini (raqamini) yuboring va men uni darhol topib beraman."
    )

@dp.message(F.text)
async def get_movie(message: types.Message):
    code = message.text.strip()
    
    # Foydalanuvchi faqat raqam kiritganini tekshiramiz
    if code.isdigit():
        movie_code = int(code)
        
        try:
            # Xabarni xatosiz yuborish uchun forward_message ishlatamiz
            await bot.forward_message(
                chat_id=message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=movie_code
            )
        except Exception as e:
            await message.answer(
                f"❌ Kechirasiz, kino topilmadi!\n\n"
                f"Sababi: Kanalingizda **{movie_code}**-raqamli xabar mavjud emas yoki u noto'g'ri ko'rsatilgan."
            )
    else:
        await message.answer("⚠️ Iltimos, kino kodini faqat raqam ko'rinishida yuboring (masalan: 2).")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot mukammal holatda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())