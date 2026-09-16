import logging
import asyncio
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8596519118:AAFANuseBfzYNxeu9k6i95xv-O5yU9zPVGc"
CHANNEL_ID = -1004452847162

# ================= SOZLAMALAR =================
ADMIN_ID = 5123456789          # <--- O'zingizning Telegram ID raqamingizni yozing!
ADMIN_USERNAME = "@yodgorov_life" # Sizning username'ingiz
CARD_NUMBER = "5614 6810 0069 4020"  # Karta raqamingiz
CARD_OWNER = "Yodgorov Azamatjon"      # Karta egasining ismi
PREMIUM_PRICE = "5 000 so'm"           # Obuna narxi

# Rasmiy kanalingiz linki
CHANNEL_LINK = "https://t.me/turkiston_kino"
# ==============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Premium foydalanuvchilar to'plami
PREMIUM_USERS = set()

# ========= RENDER UCHUN KICHIK VEB-SERVER =========
app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti va faol holatda!"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
# =================================================

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
        "• 🔍 Kino kodi orqali tezkor qidiruv (Premium uchun)\n"
        "• 🚫 Ortiqcha va zararli reklamalarsiz\n"
        "• 💎 Eksklyuziv premyeralar va yuqori sifatli videolar\n\n"
        "👉 *Marhamat, menyudan kerakli bo'limni tanlang!*"
    )
    
    await message.answer(start_text, parse_mode="Markdown", reply_markup=keyboard)

# To'lov haqida ma'lumot qismi
@dp.callback_query(F.data == "buy_premium")
async def premium_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍💻 Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
            ]
        ]
    )
    text = (
        "💎 **Premium obunaga xush kelibsiz!**\n\n"
        f"Kinolarni cheksiz ko'rish uchun 1 oylik obuna narxi: **{PREMIUM_PRICE}**\n\n"
        f"💳 To'lov uchun karta: `{CARD_NUMBER}`\n"
        f"👤 Karta egasi: **{CARD_OWNER}**\n\n"
        "✅ *To'lovni amalga oshirgach, chek rasmini shu yerga yuboring va quyidagi tugma orqali adminga ham tashlab qo'ying!*"
    )
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "search_movie")
async def search_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in PREMIUM_USERS:
        await callback.message.answer("Marhamat, ko'rmoqchi bo'lgan kino kodini yuboring! ✍️")
    else:
        await callback.message.answer(
            "🔒 **Kino qidirish uchun Premium obuna talab etiladi!**\n\n"
            f"Obuna narxi: {PREMIUM_PRICE}. To'lov qilish uchun '💎 Premium Obuna' tugmasini bosing.",
            parse_mode="Markdown"
        )
    await callback.answer()

# Foydalanuvchi chek rasmini yuborganda
@dp.message(F.photo)
async def handle_payment_check(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Adminga yuborish", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
            ]
        ]
    )
    await message.answer(
        "📥 **Chekingiz qabul qilindi!**\n\n"
        f"Iltimos, uni tezroq tasdiqlashlari uchun ushbu chekni adminga ham yuboring: {ADMIN_USERNAME}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# Admin obuna qo'shish buyrug'i: /addpremium <user_id>
@dp.message(Command("addpremium"))
async def add_premium_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return  # Faqat admin ishlatishi mumkin
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Xato! Ishlatish tartibi: `/addpremium FOYDALANUVCHI_ID`", parse_mode="Markdown")
        return
    
    try:
        target_user_id = int(args[1])
        PREMIUM_USERS.add(target_user_id)
        
        # Foydalanuvchiga xabar beramiz
        await bot.send_message(
            target_user_id,
            "🎉 **Tabriklaymiz!** Admin to'lovingizni tasdiqladi va sizga Premium obuna berildi.\n"
            "Endi kino kodlarini yuborib tomosha qilishingiz mumkin! 🎬",
            parse_mode="Markdown"
        )
        await message.answer(f"✅ `{target_user_id}` muvaffaqiyatli Premium foydalanuvchilarga qo'shildi!", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: `{e}`", parse_mode="Markdown")

# Kino qidirish va xatoni tekshirish (Faqat Premium foydalanuvchilar uchun)
@dp.message(F.text)
async def get_movie(message: types.Message):
    user_id = message.from_user.id
    
    # Premium tekshiruvi
    if user_id not in PREMIUM_USERS:
        await message.answer(
            "🔒 **Kino ko'rish uchun sizda Premium obuna yo'q!**\n\n"
            f"Obuna narxi: {PREMIUM_PRICE}. To'lov qilib, chekni yuboring va adminga murojaat qiling.",
            parse_mode="Markdown"
        )
        return

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
                f"❌ Xatolik yuz berdi (Bunday kodli kino topilmadi):\n\n`{e}`",
                parse_mode="Markdown"
            )
    else:
        await message.answer("⚠️ Iltimos, kino kodini faqat raqam ko'rinishida yuboring!")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot mukammal holatda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()  # Veb-serverni ishga tushiramiz (Render port talabi uchun)
    asyncio.run(main())
