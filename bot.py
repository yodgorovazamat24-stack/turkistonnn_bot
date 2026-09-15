import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# To'g'rilangan Token va Kanal ID
TOKEN = "8596519118:AAHYFVvax9dpJJy8s8LXAc_ZnBGnQdILMUY"
CHANNEL_ID = -100445284162

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Yangi dizayndagi /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search_movie"),
                InlineKeyboardButton(text="💎 Premium Obuna", callback_data="buy_premium")
            ],
            [
                InlineKeyboardButton(text="📢 Rasmiy Kanalimiz", url="https://t.me/SIZNING_KANALINGIZ_LINKI")
            ]
        ]
    )
    
    start_text = (
        "🎬 **Assalomu alaykum, Turkiston kino botiga xush kelibsiz!**\n\n"
        "Bu bot orqali oilangiz va o'zingiz uchun eng sara, foydali va xavfsiz kinolarni yuqori sifatda tomosha qilishingiz mumkin.\n\n"
        "📌 **Bot imkoniyatlari:**\n"
        "• 🔍 Kino kodi orqali tezkor qidiruv\n"
        "• 🚫 Ortiqcha va zararli reklamalarsiz\n"
        "• 💎 Eksklyuziv premyeralar va yuqori sifatli videolar\n\n"
        "👉 *Marhamat, ko'rmoqchi bo'lgan kinongiz kodini yuboring!*"
    )
    
    await message.answer(start_text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "buy_premium")
async def premium_callback(callback: types.CallbackQuery):
    await callback.answer("Tez kunda ishga tushadi! 🚀", show_alert=True)

@dp.callback_query(F.data == "search_movie")
async def search_callback(callback: types.CallbackQuery):
    await callback.message.answer("Marhamat, kino kodini yuboring! ✍️")
    await callback.answer()

# Kinoni forward qilmasdan, toza copy_message orqali yuborish
@dp.message(F.text)
async def get_movie(message: types.Message):
    code = message.text.strip()
    
    if code.isdigit():
        movie_code = int(code)
        
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=movie_code
            )
        except Exception as e:
            await message.answer(
                f"❌ Kechirasiz, kino topilmadi!\n\n"
                f"Sababi: Kanalingizda **{movie_code}**-raqamli xabar mavjud emas yoki noto'g'ri kod kiritdingiz."
            )
    else:
        await message.answer("⚠️ Iltimos, kino kodini faqat raqam ko'rinishida yuboring!")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot mukammal holatda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
