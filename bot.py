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

# Foydalanuvchilarning oxirgi qidiruv natijalarini saqlash uchun
USER_SEARCH_RESULTS = {}

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
    await callback.message.edit_text("🎵 Qidirayotgan qo'shig'ingiz yoki xonanda nomini yuboring (masalan: *Benom* yoki *Konsta*):", parse_mode="Markdown", reply_markup=keyboard)
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

    # 1. Havola bo'lsa -> Videoni yuklab berish
    if text.startswith("http://") or text.startswith("https://"):
        processing_msg = await message.answer("⏳ Video yuklab olinmoqda, iltimos kuting...")
        
        output_template = "video.mp4"
        ydl_opts = {
            'format': 'best[filesize<50M]/best',
            'outtmpl': output_template,
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        }

        try:
            def download_video():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([text])
            
            await asyncio.to_thread(download_video)
            video_file = types.FSInputFile(output_template)
            
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

    # 2. Raqam bo'lsa -> Kino kodini qidirish
    elif text.isdigit():
        movie_code = int(text)
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=movie_code,
                protect_content=True
            )
        except Exception as e:
            await message.answer(
                f"❌ Xatolik yuz berdi (Bunday kodli kino topilmadi):\n\n`{e}`",
                parse_mode="Markdown"
            )

    # 3. Oddiy matn bo'lsa -> SoundCloud orqali qo'shiq qidirish va kuchaytirilgan spam filtrlash
    else:
        processing_msg = await message.answer("🎵 Qo'shiqlar qidirilmoqda, iltimos kuting...")
        try:
            ydl_opts = {
                'extract_flat': True,
                'skip_download': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            }
            def search_songs():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"scsearch25:{text}", download=False)
            
            info = await asyncio.to_thread(search_songs)
            entries = info.get('entries', [])

            if not entries:
                await processing_msg.edit_text("❌ Hech qanday qo'shiq topilmadi.")
                return
                
            result_text = f"🔍 <b>Qidiruv natijasi: {text}</b>\n\n"
            video_ids = []
            
            for entry in entries:
                title = entry.get('title', '')
                url = entry.get('webpage_url') or entry.get('url', '')
                description = entry.get('description', '')
                
                # Matnlarni kichik harfga o'tkazib tekshiramiz
                combined_text = (title + " " + description + " " + str(url)).lower()
                
                # Kuchaytirilgan reklama va spam so'zlar ro'yxati
                spam_keywords = [
                    't.me', 'telegram', 'a_toolsx', 'must join', 
                    'subscribe', 'bot', 'channel', 'официальный канал', 
                    'подпишись', 'реклама', 'кanal', 'obuna', 'join'
                ]
                
                # Agar matnda reklama so'zlari bo'lsa, uni tashlab yuboramiz
                if any(word in combined_text for word in spam_keywords):
                    continue
                
                if not title or not url:
                    continue
                
                # Havolani to'g'rilash
                if not str(url).startswith('http'):
                    url = "https://soundcloud.com" + str(url)
                
                if len(video_ids) < 10:
                    video_ids.append(url)
                    idx_num = len(video_ids)
                    result_text += f"<b>{idx_num}.</b> {title}\n"
                
                if len(video_ids) >= 10:
                    break

            if not video_ids:
                await processing_msg.edit_text("❌ Afsuski, bu so'rov bo'yicha toza qo'shiqlar topilmadi.")
                return

            USER_SEARCH_RESULTS[user_id] = video_ids
            
            row1 = [InlineKeyboardButton(text=str(i), callback_data=f"song_idx_{user_id}_{i-1}") for i in range(1, 6) if i <= len(video_ids)]
            row2 = [InlineKeyboardButton(text=str(i), callback_data=f"song_idx_{user_id}_{i-1}") for i in range(6, 11) if i <= len(video_ids)]
            cancel_row = [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_search")]
            
            keyboard_layout = []
            if row1: keyboard_layout.append(row1)
            if row2: keyboard_layout.append(row2)
            keyboard_layout.append(cancel_row)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
            
            await processing_msg.edit_text(result_text, parse_mode="HTML", reply_markup=keyboard)
        except Exception as e:
            await processing_msg.edit_text(f"❌ Qidirishda xatolik yuz berdi: {e}")

# Raqamli tugma bosilganda qo'shiqni yuklab berish
@dp.callback_query(F.data.startswith("song_idx_"))
async def download_indexed_song(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    idx = int(parts[3])
    
    current_user_id = callback.from_user.id
    
    if current_user_id != target_user_id:
        await callback.answer("❌ Bu tugma boshqa foydalanuvchiga tegishli!", show_alert=True)
        return

    if current_user_id not in USER_SEARCH_RESULTS or idx >= len(USER_SEARCH_RESULTS[current_user_id]):
        await callback.answer("❌ Qidiruv eskirgan. Iltimos, qo'shiqni qaytadan qidiring.", show_alert=True)
        return
        
    song_url = USER_SEARCH_RESULTS[current_user_id][idx]
    
    status_msg = await callback.message.answer("⏳ Tanlangan qo'shiq yuklab olinmoqda, iltimos kuting...")
    
    output_template = f"song_{current_user_id}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template.replace('.mp3', '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'max_filesize': 50 * 1024 * 1024,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    try:
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song_url])
        
        await asyncio.to_thread(download_audio)
        actual_file = f"song_{current_user_id}.mp3"
        
        if os.path.exists(actual_file):
            audio_file = types.FSInputFile(actual_file)
            caption_text = (
                "🎵 **Marhamat, siz so'ragan qo'shiq!**\n\n"
                "📥 *Musiqa yuklab oluvchi bot: @turkiston_bot*"
            )
            await callback.message.answer_audio(audio=audio_file, caption=caption_text, parse_mode="Markdown")
            os.remove(actual_file)
        else:
            await callback.message.answer("❌ Qo'shiq faylini tayyorlab bo'lmadi.")
            
        await status_msg.delete()
        await callback.answer()
    except Exception as e:
        await status_msg.edit_text(f"❌ Qo'shiqni yuklab bo'lmadi.\n\nXatolik: {e}")

@dp.callback_query(F.data == "cancel_search")
async def cancel_search_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Qidiruv bekor qilindi.")
    await callback.answer()

@dp.callback_query(F.data == "check_sub")
async def recheck_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscriptions(user_id)
    
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
