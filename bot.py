import logging
import asyncio
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8596519118:AAF-Yw3Oz5aHO7Fs_29mHgu-4Y4G9hA-6GU"
CHANNEL_ID = -1004452847162  # Kino bazasi joylashgan yopiq kanal

# ================= SOZLAMALAR =================
ADMIN_ID = 5144043830
ADMIN_USERNAME = "@yodgorov_life"

# Majburiy obuna qilinishi kerak bo'lgan kanallar
REQUIRED_CHANNELS = [
    {"username": "@zayafka154", "url": "https://t.me/zayafka154"},
    {"username": "@zakafka289", "url": "https://t.me/zakafka289"}
]
# ==============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Jami start bosgan foydalanuvchilar bazasi
ALL_USERS = set()

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

# Foydalanuvchi kanallarga obuna bo'lganini tekshiruvchi funksiya
async def check_subscriptions(user_id: int) -> bool:
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

# /start komandasi va menyu
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    ALL_USERS.add(user_id)  
    
    if user_id == ADMIN_ID:
        await message.answer("🛠 *Admin ekanligingiz aniqlandi.*\nAdmin panelni ochish uchun 👉 /admin", parse_mode="Markdown")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search_movie")
            ]
        ]
    )
    
    start_text = (
        "🎬 **Assalomu alaykum, Turkiston kino botiga xush kelibsiz!**\n\n"
        "Kinoni ko'rish uchun quyidagi shartlarni bajarib, kino kodini yuboring.\n\n"
        "👉 *Marhamat, menyudan kerakli bo'limni tanlang!*"
    )
    
    await message.answer(start_text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "search_movie")
async def search_callback(callback: types.CallbackQuery):
    await callback.message.answer("Marhamat, ko'rmoqchi bo'lgan kino kodini yuboring! ✍️")
    await callback.answer()
    
    # Orqaga qaytish tugmasi
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
# ================= ADMIN PANEL BUYRUQLARI =================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = (
        "👑 **ADMIN PANEL**\n\n"
        "📊 **Statistikani ko'rish:**\n"
        "`/stats`"
    )
    await message.answer(text, parse_mode="Markdown")

# Statistika (Jami obunachilar)
@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = (
        "📊 **BOT STATISTIKASI**\n\n"
        f"👥 Jami obunachilar (Start bosganlar): **{len(ALL_USERS)} ta**"
    )
    await message.answer(text, parse_mode="Markdown")

# ====================================================

# Kino qidirish va obunani tekshirish
@dp.message(F.text)
async def get_movie(message: types.Message):
    user_id = message.from_user.id
    
    is_subscribed = await check_subscriptions(user_id)
    
    if not is_subscribed:
        keyboard_buttons = []
        for idx, ch in enumerate(REQUIRED_CHANNELS, 1):
            keyboard_buttons.append([InlineKeyboardButton(text=f"📢 {idx}-kanalga obuna bo'lish", url=ch["url"])])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔄 Obunani tekshirish", callback_data="check_sub")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            "⚠️ **Kino olish uchun quyidagi kanallarga obuna bo'lishingiz shart!**\n\n"
            "Iltimos, kanallarga a'zo bo'lib, so'ng **'🔄 Obunani tekshirish'** tugmasini bosing:",
            parse_mode="Markdown",
            reply_markup=keyboard
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

@dp.callback_query(F.data == "check_sub")
async def recheck_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscriptions(user_id)
    
    if is_subscribed:
        await callback.message.edit_text("✅ Tabriklaymiz, obuna tasdiqlandi! Endi istalgan kino kodini yuborishingiz mumkin.")
    else:
        await callback.answer("❌ Siz hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot mukammal holatda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
