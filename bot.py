import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8596519118:AAFANuseBfzYNxeu9k6i95xv-O5yU9zPVGc"
CHANNEL_ID = -1004452847162

# ================= SOZLAMALAR =================
CARD_NUMBER = "5614 6810 0069 4020"  # Karta raqamingiz
CARD_OWNER = "Yodgorov Azamatjon"     # Karta egasining ismi

# Rasmiy kanalingiz linki
CHANNEL_LINK = "https://t.me/turkiston_kino"
# ==============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# /start komandasi va menyu
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search_movie"),
                InlineKeyboardButton(text="💎 Premium Obuna", callback_data="buy_premium")
            ],
            [
                InlineKeyboardButton(text="📢 Rasmiy Kanalimiz", url=CHANNEL_LINK)
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

# To'lov haqida ma'lumot qismi
@dp.callback_query(F.data == "buy_premium")
async def premium_callback(callback: types.CallbackQuery):
    text = (
        "💎 **Premium obunaga xush kelibsiz!**\n\n"
        "Premium orqali siz eng so'nggi va sara kinolarni tomosha qilishingiz mumkin bo'ladi.\n\n"
        f"💳 To'lov uchun karta: `{CARD_NUMBER}`\n"
        f"👤 Karta egasi: **{CARD_OWNER}**\n\n"
        "✅ *To'lov qilganingizdan so'ng, to'lov cheki skrinshotini adminga yuboring!*"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "search_movie")
async def search_callback(callback: types.CallbackQuery):
    await callback.message.answer("Marhamat, kino kodini yuboring! ✍️")
    await callback.answer()

# Kino qidirish va xatoni tekshirish
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
                f"❌ Xatolik yuz berdi:\n\n`{e}`\n\n"
                "_(Kino nima uchun chiqmayotganini aniqlashimiz uchun shu xabar ko'rsatilmoqda)_",
                parse_mode="Markdown"
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
