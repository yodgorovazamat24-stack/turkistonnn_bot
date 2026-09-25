import logging
import asyncio
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

TOKEN = "8596519118:AAFyFGwcAPtBoXMzSrI5ZqsHcxFSeJJ456s"
CHANNEL_ID = -1004452847162  # Kino bazasi joylashgan yopiq kanal

# ================= SOZLAMALAR =================
ADMIN_ID = 5144043830
ADMIN_USERNAME = "@yodgorov_life"

# Majburiy obuna qilinishi kerak bo'lgan kanallar
REQUIRED_CHANNELS = ["@zakafka289", "@zayafka154"]
# ==============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Jami start bosgan foydalanuvchilar bazasi
ALL_USERS = set()

# Foydalanuvchilarning oxirgi qidiruv natijalarini va qo'shiq nomlarini saqlash uchun
USER_SEARCH_RESULTS = {}
USER_SEARCH_TITLES = {}
USER_CURRENT_PAGE = {}

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

# Asosiy menyu tugmalari
def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="search_movie")],
            [InlineKeyboardButton(text="📥 Video yuklab olish", callback_data="download_video_menu")],
            [InlineKeyboardButton(text="🎵 Qo'shiq qidirish", callback_data="search_song_menu")]
        ]
    )

# ========= BOT PROFILIDAGI FOYDALANUVCHILAR SONINI YANGILASH =========
async def update_bot_about():
    try:
        total_users = len(ALL_USERS)
        new_about = f"🎬 Kino, Video va Musiqa boti.\n👥 Foydalanuvchilar: {total_users} ta"
        await bot.set_my_short_description(short_description=new_about)
    except Exception as e:
        print(f"About qismini yangilashda xatolik: {e}")

# ========= MAJBURIY OBUNANI TEKSHIRISH FUNKSIYASI =========
async def check_user_subscriptions(user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Kanalni tekshirishda xatolik {channel}: {e}")
            return False
    return True

async def send_subscription_widget(message_or_callback):
    builder = InlineKeyboardBuilder()
    for ch in REQUIRED_CHANNELS:
        clean_ch = ch.replace('@', '')
        builder.button(text=f"📢 Kanalga obuna bo'lish", url=f"https://t.me/{clean_ch}")
    builder.button(text="✅ Obunani tekshirish", callback_data="check_sub")
    builder.adjust(1)
    
    text = (
        "⚠️ **Botimizdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak:**\n\n"
        "Kanallarga a'zo bo'lgach, **«✅ Obunani tekshirish»** tugmasini bosing!"
    )
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    elif isinstance(message_or_callback, types.CallbackQuery):
        try:
            await message_or_callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
        except Exception:
            await message_or_callback.message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    ALL_USERS.add(user_id)  
    
    # Bot profilidagi statistika sonini yangilash
    await update_bot_about()
    
    if not await check_user_subscriptions(user_id):
        await send_subscription_widget(message)
        return

    if user_id == ADMIN_ID:
        await message.answer("🛠 *Admin ekanligingiz aniqlandi.*\nAdmin panelni ochish uchun 👉 /admin", parse_mode="Markdown")

    start_text = (
        "🎬 **Assalomu alaykum, botimizga xush kelibsiz!**\n\n"
        "Quyidagi menyudan o'zingizga kerakli xizmatni tanlang:\n\n"
        "• *Kino qidirish* — Kino kodini yuborish orqali kinolarni oling.\n"
        "• *Video yuklab olish* — Instagram va TikTok tarmoqlaridan video havolasini yuboring.\n"
        "• *Qo'shiq qidirish* — Musiqa yoki qo'shiq nomini yuboring."
    )
    
    await message.answer(start_text, parse_mode="Markdown", reply_markup=get_main_menu())

# Obunani tekshirish tugmasi
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_user_subscriptions(user_id):
        await callback.answer("✅ Rahmat, kanallarga obuna bo'lgansiz!", show_alert=True)
        start_text = (
            "🎬 **Assalomu alaykum, botimizga xush kelibsiz!**\n\n"
            "Quyidagi menyudan o'zingizga kerakli xizmatni tanlang:"
        )
        try:
            await callback.message.edit_text(start_text, parse_mode="Markdown", reply_markup=get_main_menu())
        except Exception:
            await callback.message.answer(start_text, parse_mode="Markdown", reply_markup=get_main_menu())
    else:
        await callback.answer("❌ Siz hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

# Tugmalar bo'yicha yo'naltirishlar
@dp.callback_query(F.data == "search_movie")
async def search_callback(callback: types.CallbackQuery):
    if not await check_user_subscriptions(callback.from_user.id):
        await send_subscription_widget(callback)
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text("Marhamat, ko'rmoqchi bo'lgan **kino kodini** (raqam) yuboring! ✍️", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "download_video_menu")
async def download_video_callback(callback: types.CallbackQuery):
    if not await check_user_subscriptions(callback.from_user.id):
        await send_subscription_widget(callback)
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text("📥 Menga **Instagram** yoki **TikTok** video havolasini (linkini) yuboring, men uni sizga yuklab beraman!", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "search_song_menu")
async def search_song_callback(callback: types.CallbackQuery):
    if not await check_user_subscriptions(callback.from_user.id):
        await send_subscription_widget(callback)
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text("🎵 Qidirayotgan qo'shig'ingiz yoki xonanda nomini yuboring (masalan: *Benom* yoki *Konsta*):", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start_callback(callback: types.CallbackQuery):
    if not await check_user_subscriptions(callback.from_user.id):
        await send_subscription_widget(callback)
        return
    start_text = (
        "🎬 **Assalomu alaykum, botimizga xush kelibsiz!**\n\n"
        "Quyidagi menyudan o'zingizga kerakli xizmatni tanlang:"
    )
    await callback.message.edit_text(start_text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

# ================= ADMIN PANEL =================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = (
        "👑 **ADMIN PANEL**\n\n"
        "📊 Bot statistikasini ko'rish uchun quyidagi buyruqdan foydalaning:\n"
        "👉 /stats"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = f"📊 **BOT STATISTIKASI**\n\n👥 Jami obunachilar (Start bosganlar): **{len(ALL_USERS)} ta**"
    await message.answer(text, parse_mode="Markdown")

# ================= SAHIFALASH (PAGINATION) =================
def generate_search_keyboard(user_id: int, page: int, total_pages: int, current_items_count: int):
    keyboard_layout = []
    row1 = []
    row2 = []
    for i in range(1, current_items_count + 1):
        btn = InlineKeyboardButton(text=str(i), callback_data=f"song_idx_{user_id}_{i-1}")
        if i <= 5:
            row1.append(btn)
        else:
            row2.append(btn)
            
    if row1: keyboard_layout.append(row1)
    if row2: keyboard_layout.append(row2)
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"song_page_{user_id}_{page-1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingisi ➡️", callback_data=f"song_page_{user_id}_{page+1}"))
        
    if nav_row:
        keyboard_layout.append(nav_row)
        
    keyboard_layout.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_search")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_layout)

def get_page_content(user_id: int, page: int):
    urls = USER_SEARCH_RESULTS.get(user_id, [])
    titles = USER_SEARCH_TITLES.get(user_id, [])
    start_idx = page * 5
    end_idx = start_idx + 5
    return urls[start_idx:end_idx], titles[start_idx:end_idx]

# ================= XABARLAR BILAN ISHLASH (HANDLER) =================

@dp.message(F.text)
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_user_subscriptions(user_id):
        await send_subscription_widget(message)
        return

    text = message.text.strip()

    # Video yuklab olish (Instagram / TikTok)
    if text.startswith("http://") or text.startswith("https://"):
        processing_msg = await message.answer("⏳ Video yuklab olinmoqda, iltimos kuting...")
        
        output_template = "video.mp4"
    ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        }

        try:
            def download_video():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([text])
            
            await asyncio.to_thread(download_video)
            video_file = types.FSInputFile(output_template)
            
            caption_text = (
                "✅ **Marhamat, siz so'ragan video!**\n\n"
                "📥 *Video yuklab oluvchi bot: @turkistonn_bot*\n"
                "🎬 *Oila va bolalar uchun sara kinolar bazasi*"
            )
            
            await message.answer_video(video=video_file, caption=caption_text, parse_mode="Markdown")
            
            if os.path.exists(output_template):
                os.remove(output_template)
                
            await processing_msg.delete()
        except Exception as e:
            await processing_msg.edit_text(f"❌ Videoni yuklab bo'lmadi. Havola noto'g'ri yoki hajmi juda katta.\n\nXatolik: {e}")

    # Kino kodi orqali qidirish
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

    # Qo'shiq qidirish
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
                    return ydl.extract_info(f"scsearch30:{text}", download=False)
            
            info = await asyncio.to_thread(search_songs)
            entries = info.get('entries', [])

            if not entries:
                await processing_msg.edit_text("❌ Hech qanday qo'shiq topilmadi.")
                return
                
            video_ids = []
            video_titles = []
            
            for entry in entries:
                title = entry.get('title', '')
                url = entry.get('webpage_url') or entry.get('url', '')
                
                if not title or not url:
                    continue
                
                if not str(url).startswith('http'):
                    url = "https://soundcloud.com" + str(url)
                
                if url not in video_ids:
                    video_ids.append(url)
                    video_titles.append(title)
                
                if len(video_ids) >= 15:
                    break

            if not video_ids:
                await processing_msg.edit_text("❌ Afsuski, bu so'rov bo'yicha qo'shiqlar topilmadi.")
                return

            USER_SEARCH_RESULTS[user_id] = video_ids
            USER_SEARCH_TITLES[user_id] = video_titles
            
            page = 0
            USER_CURRENT_PAGE[user_id] = page
            total_pages = (len(video_ids) + 4) // 5
            
            page_urls, page_titles = get_page_content(user_id, page)
            
            result_text = f"🔍 <b>Qidiruv natijasi: {text}</b> (Sahifa {page+1}/{total_pages})\n\n"
            for idx, title in enumerate(page_titles, 1):
                result_text += f"<b>{idx}.</b> {title}\n"
                
            keyboard = generate_search_keyboard(user_id, page, total_pages, len(page_urls))
            await processing_msg.edit_text(result_text, parse_mode="HTML", reply_markup=keyboard)
        except Exception as e:
            await processing_msg.edit_text(f"❌ Qidirishda xatolik yuz berdi: {e}")

@dp.callback_query(F.data.startswith("song_page_"))
async def change_song_page(callback: types.CallbackQuery):
    if not await check_user_subscriptions(callback.from_user.id):
        await send_subscription_widget(callback)
        return
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    page = int(parts[3])
    
    if callback.from_user.id != target_user_id:
        await callback.answer("❌ Bu tugma boshqa foydalanuvchiga tegishli!", show_alert=True)
        return
        
    urls = USER_SEARCH_RESULTS.get(target_user_id, [])
    titles = USER_SEARCH_TITLES.get(target_user_id, [])
    
    if not urls:
        await callback.answer("❌ Qidiruv muddati tugagan. Qaytadan qidiring.", show_alert=True)
        return
        
    USER_CURRENT_PAGE[target_user_id] = page
    total_pages = (len(urls) + 4) // 5
    page_urls, page_titles = get_page_content(target_user_id, page)
    
    result_text = f"🔍 <b>Qidiruv natijalari</b> (Sahifa {page+1}/{total_pages})\n\n"
    for idx, title in enumerate(page_titles, 1):
        result_text += f"<b>{idx}.</b> {title}\n"
        
    keyboard = generate_search_keyboard(target_user_id, page, total_pages, len(page_urls))
    
    try:
        await callback.message.edit_text(result_text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()

@dp.callback_query(F.data == "noop")
async def noop_callback(callback: types.CallbackQuery):
    await callback.answer()

@dp.callback_query(F.data.startswith("song_idx_"))
async def download_indexed_song(callback: types.CallbackQuery):
    if not await check_user_subscriptions(callback.from_user.id):
        await send_subscription_widget(callback)
        return
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    local_idx = int(parts[3])
    
    current_user_id = callback.from_user.id
    
    if current_user_id != target_user_id:
        await callback.answer("❌ Bu tugma boshqa foydalanuvchiga tegishli!", show_alert=True)
        return

    urls = USER_SEARCH_RESULTS.get(current_user_id, [])
    current_page = USER_CURRENT_PAGE.get(current_user_id, 0)
    global_idx = (current_page * 5) + local_idx
    
    if current_user_id not in USER_SEARCH_RESULTS or global_idx >= len(urls):
        await callback.answer("❌ Qidiruv eskirgan. Iltimos, qo'shiqni qaytadan qidiring.", show_alert=True)
        return
        
    song_url = urls[global_idx]
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
                "📥 *Musiqa yuklab oluvchi bot: @turkistonn_bot*"
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

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot mukammal holatda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
