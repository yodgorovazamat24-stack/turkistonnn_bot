import logging
import asyncio
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

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

# Asosiy menyu tugmalari
def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search_movie")],
            [InlineKeyboardButton(text="📥 Video yuklab olish", callback_data="download_video_menu")],
            [InlineKeyboardButton(text="🎵 Qo'shiq qidirish", callback_data="search_song_menu")]
        ]
    )

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    ALL_USERS.add(user_id)  
    
    if user_id == ADMIN_ID:
        await message.answer("🛠 *Admin ekanligingiz aniqlandi.*\nAdmin panelni ochish uchun 👉 /admin", parse_mode="Markdown")

    start_text = (
        "🎬 **Assalomu alaykum, Turkiston botiga xush kelibsiz!**\n\n"
        "Quyidagi menyudan o'zingizga kerakli xizmatni tanlang:\n\n"
        "• *Kino qidirish* — Kino kodini yuborish orqali kinolarni oling.\n"
        "• *Video yuklab olish* — Instagram va TikTok tarmoqlaridan video havolasini yuboring.\n"
        "• *Qo'shiq qidirish* — Musiqa yoki qo'shiq nomini yuboring."
    )
    
    await message.answer(start_text, parse_mode="Markdown", reply_markup=get_main_menu())

# Tugmalar bo'yicha yo'naltirishlar
@dp.callback_query(F.data == "search_movie")
async def search_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text("Marhamat, ko'rmoqchi bo'lgan **kino kodini** (raqam) yuboring! ✍️", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "download_video_menu")
async def download_video_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text("📥 Menga **Instagram** yoki **TikTok** video havolasini (linkini) yuboring, men uni sizga yuklab beraman!", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "search_song_menu")
async def search_song_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text("🎵 Qidirayotgan qo'shig'ingiz yoki xonanda nomini yuboring (masalan: *Konsta* yoki *Yurak*):", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start_callback(callback: types.CallbackQuery):
    start_text = (
        "🎬 **Assalomu alaykum, Turkiston botiga xush kelibsiz!**\n\n"
        "Quyidagi menyudan o'zingizga kerakli xizmatni tanlang:"
    )
    await callback.message.edit_text(start_text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

# ================= ADMIN PANEL =================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = "👑 **ADMIN PANEL**\n\n📊 Statistikani ko'rish uchun: `/stats`"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = f"📊 **BOT STATISTIKASI**\n\n👥 Jami obunachilar (Start bosganlar): **{len(ALL_USERS)} ta**"
    await message.answer(text, parse_mode="Markdown")

# ================= XABARLAR BILAN ISHLASH (HANDLER) =================

@dp.message(F.text)
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    
    # Obunani tekshirish
    is_subscribed = await check_subscriptions(user_id)
    if not is_subscribed:
        keyboard_buttons = []
        for idx, ch in enumerate(REQUIRED_CHANNELS, 1):
            keyboard_buttons.append([InlineKeyboardButton(text=f"📢 {idx}-kanalga obuna bo'lish", url=ch["url"])])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔄 Obunani tekshirish", callback_data="check_sub")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            "⚠️ **Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart!**\n\n"
            "Iltimos, kanallarga a'zo bo'lib, so'ng **'🔄 Obunani tekshirish'** tugmasini bosing:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return

    text = message.text.strip()

    # 1. Agar yuborilgan matn havola (link) bo'lsa -> Videoni yuklab berish
    if text.startswith("http://") or text.startswith("https://"):
        processing_msg = await message.answer("⏳ Video yuklab olinmoqda, iltimos kuting...")
        
        output_template = "video.mp4"
        ydl_opts = {
            'format': 'best[filesize<50M]/best',
            'outtmpl': output_template,
        }

        try:
            def download_video():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([text])
            
            await asyncio.to_thread(download_video)
            
            video_file = types.FSInputFile(output_template)
        
            # Reklama matni va bot havolasi
            caption_text = (
                "✅ **Marhamat, siz so'ragan video!**\n\n"
                "📥 *Video yuklab oluvchi bot: @turkiston_bot*\n"
                "🎬 *Kino va videolar bazasi*"
            )
            
            await message.answer_video(video=video_file, caption=caption_text, parse_mode="Markdown")
            
            if os.path.exists(output_template):
                os.remove(output_template)
                
            await processing_msg.delete()
        except Exception as e:
            await processing_msg.edit_text(f"❌ Videoni yuklab bo'lmadi. Havola noto'g'ri yoki hajmi juda katta.\n\nXatolik: {e}")

    # 2. Agar yuborilgan matn raqam bo'lsa -> Kino kodini qidirish (Forward qilib bo'lmaydigan qilib)
    elif text.isdigit():
        movie_code = int(text)
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=movie_code,
                protect_content=True  # Boshqalarga ulashish va saqlashni bloklash
            )
        except Exception as e:
            await message.answer(
                f"❌ Xatolik yuz berdi (Bunday kodli kino topilmadi):\n\n`{e}`",
                parse_mode="Markdown"
            )

    # 3. Agar oddiy matn bo'lsa -> Qo'shiq qidirish (10 ta variant chiqarish)
    else:
        processing_msg = await message.answer("🎵 Qo'shiqlar qidirilmoqda, iltimos kuting...")
        try:
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
            }
            def search_songs():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch10:{text}", download=False)
            
            info = await asyncio.to_thread(search_songs)
            entries = info.get('entries', [])
            
            if not entries:
                await processing_msg.edit_text("❌ Hech qanday qo'shiq topilmadi.")
                return
                
            keyboard_buttons = []
            for entry in entries[:10]:
                title = entry.get('title', 'Nomaʼlum qoʻshiq')
                video_id = entry.get('id')
                if title and video_id:
                    short_title = title[:40] + "..." if len(title) > 40 else title
                    keyboard_buttons.append([InlineKeyboardButton(text=f"🎵 {short_title}", callback_data=f"song_{video_id}")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await processing_msg.edit_text(f"🔍 *{text}* bo'yicha topilgan qo'shiqlar:", parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            await processing_msg.edit_text(f"❌ Qidirishda xatolik yuz berdi: {e}")

# Qo'shiq tugmasi bosilganda yuklab berish
@dp.callback_query(F.data.startswith("song_"))
async def download_song_callback(callback: types.CallbackQuery):
    video_id = callback.data.split("_")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    await callback.message.edit_text("⏳ Tanlangan qo'shiq yuklab olinmoqda, iltimos kuting...")
    
    output_template = f"song_{video_id}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template.replace('.mp3', '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'max_filesize': 50 * 1024 * 1024,
    }
    
    try:
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        
        await asyncio.to_thread(download_audio)
        
        actual_file = f"song_{video_id}.mp3"
        
        if os.path.exists(actual_file):
            audio_file = types.FSInputFile(actual_file)
            caption_text = (
                "🎵 *Marhamat, siz so'ragan qo'shiq!*\n\n"
                "📥 *Musiqa yuklab oluvchi bot: @turkiston_bot*"
            )
            await callback.message.answer_audio(audio=audio_file, caption=caption_text, parse_mode="Markdown")
            os.remove(actual_file)
        else:
            await callback.message.answer("❌ Qo'shiq faylini tayyorlab bo'lmadi.")
            
        await callback.message.delete()
    except Exception as e:
        await callback.message.edit_text(f"❌ Qo'shiqni yuklab bo'lmadi. Hajmi katta yoki xatolik yuz berdi.\n\nXatolik: {e}")

@dp.callback_query(F.data == "check_sub")
async def recheck_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscriptions(user_id)
    
    if is_subscribed:
        await callback.message.edit_text("✅ Tabriklaymiz, obuna tasdiqlandi! Endi istalgan xizmatdan foydalanishingiz mumkin.", reply_markup=get_main_menu())
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
