import logging
import asyncio
import sqlite3
from datetime import datetime
import csv
import os
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BotCommand, BotCommandScopeChat
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Environment variables (for deployment) or default values (for local development)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8352576394:AAFYj40ivuNoW0NRfI4nQ-xUEE588ARqfqw")
ADMIN_ID = int(os.getenv("ADMIN_ID", "817765302"))
EXCEL_FILE = os.getenv("EXCEL_FILE", "tasdiqlangan_sertifikatlar.csv")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegistrationStates(StatesGroup):
    waiting_full_name = State()
    waiting_details = State()
    waiting_confirmation = State()

class AdminStates(StatesGroup):
    waiting_certificate_photo = State()
    waiting_send_confirmation = State()
    waiting_message_id = State()
    waiting_message_text = State()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

START_MESSAGE = """📜 <b>Assalomu alaykum!</b>

Men — <b>A.Y.P.I Sertifikat Botiman</b> 🤖

A.Y.P.I kursini tamomlaganlar uchun rasmiy sertifikat beramiz! 📜✨"""

WARNING_MESSAGE = """🛑🛑🛑 <b>JIDDIY OGOHLANTIRISH!</b> 🛑🛑🛑

⚖️ <b>QONUNIY OGOHLANTIRISH</b>

Bu bot A.Y.P.I platformasining RASMIY sertifikat tizimi!

🚫 <b>QATTIQ TAQIQLANADI:</b>

❌ Yolg'on ma'lumot berish
❌ Boshqa odamning nomidan ro'yxatdan o'tish
❌ O'yin yoki sinov maqsadida foydalanish
❌ Firibgarlik va aldash

⚖️ <b>JINOIY JAVOBGARLIK:</b>

O'zbekiston Respublikasi Jinoyat Kodeksi:
• <b>168-modda:</b> Firibgarlik
• <b>159-modda:</b> Hujjatlarni qalbakilashtirish

🔴 <b>BU BOTDAN FOYDALANISH SHARTLARI:</b>

1️⃣ Siz A.Y.P.I kursini HAQIQATAN tamomlagansiz
2️⃣ Barcha ma'lumotlar TO'G'RI va ANIQ
3️⃣ Faqat 1 MARTA foydalanish huquqingiz bor
4️⃣ Yolg'on aniqlansa - DARHOL CHETLASHTIRILASIZ

⚠️ <b>ADMIN TEKSHIRADI:</b>

Barcha ma'lumotlaringiz admin tomonidan qat'iy tekshiriladi. Yolg'on topilsa:

❌ Sertifikat berilmaydi
❌ Kursdan chetlashtirilasiz
❌ Qaytadan qatnashish mumkin emas
❌ Qora ro'yxatga tushirilasiz

✅ <b>FAQAT HALOL VA TO'G'RI BO'LING!</b>

Davom etsangiz, barcha shartlarga ROZLIGINGIZNI bildirgan bo'lasiz!"""

CONGRATS_MESSAGE = """🎉 <b>Tabriklaymiz!</b>

A.Y.P.I kursini muvaffaqiyatli tamomlagan ekansiz! 👏

YouTube'da katta ishlar qilishingiz va ulkan zafarlar qozonishingiz uchun chin dildan omad tilaymiz! 🚀

Endi rasmiy sertifikatingizni olish uchun quyidagi ma'lumotlarni yuboring:"""

CERTIFICATE_SUCCESS_MESSAGE = """🎉🎉🎉 <b>TABRIKLAYMIZ!</b> 🎉🎉🎉

✅ <b>Rasmiy sertifikatingiz tayyor!</b>

🌟 YouTube'da katta ishlar qilishingiz, ulkan zafarlar qozonishingiz va muvaffaqiyatli bo'lishingiz uchun chin dildan omad tilaymiz!

💪 Har doim oldinga intiling va o'z maqsadlaringizga erishing!

🚀 Katta yutuqlarga erishishingizga ishonchimiz komil!

Siz bilan faxrlanamiz! 🤝

— <b>Oybek Bozorov va A.Y.P.I Jamoasi</b> 💙"""

def init_db():
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS certificate_requests (
        id INTEGER PRIMARY KEY, 
        user_id INTEGER, 
        username TEXT, 
        full_name TEXT, 
        guruh TEXT,
        telefon TEXT, 
        telegram_username TEXT,
        status TEXT DEFAULT 'pending', 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        approved_at TIMESTAMP,
        certificate_sent_at TIMESTAMP
    )''')
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

def init_excel():
    if not os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                '№', 
                'Telegram ID', 
                'Username', 
                'Ism Familiya', 
                'Guruh',
                'Telefon',
                'Telegram Username',
                'Ariza Yaratilgan',
                'Tasdiqlangan Vaqt',
                'Sertifikat Yuborilgan'
            ])
        logger.info(f"✅ Excel fayl yaratildi: {EXCEL_FILE}")

def save_request(data):
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute("""INSERT INTO certificate_requests 
        (user_id, username, full_name, guruh, telefon, telegram_username) 
        VALUES (?,?,?,?,?,?)""", 
        (data['user_id'], data['username'], data['full_name'], 
         data['guruh'], data['telefon'], data['telegram_username']))
    request_id = c.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"✅ So'rov saqlandi: #{request_id}")
    return request_id

def get_request(request_id):
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM certificate_requests WHERE id=?", (request_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0], 
            'user_id': row[1], 
            'username': row[2], 
            'full_name': row[3], 
            'guruh': row[4],
            'telefon': row[5],
            'telegram_username': row[6],
            'status': row[7], 
            'created_at': row[8], 
            'approved_at': row[9],
            'certificate_sent_at': row[10]
        }

def update_status(request_id, status):
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    if status == 'approved':
        c.execute("""UPDATE certificate_requests 
            SET status=?, approved_at=CURRENT_TIMESTAMP 
            WHERE id=?""", (status, request_id))
    else:
        c.execute("""UPDATE certificate_requests 
            SET status=? 
            WHERE id=?""", (status, request_id))
    conn.commit()
    conn.close()
    logger.info(f"✅ Status yangilandi: #{request_id} -> {status}")

def mark_certificate_sent(request_id):
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute("""UPDATE certificate_requests 
        SET certificate_sent_at=CURRENT_TIMESTAMP 
        WHERE id=?""", (request_id,))
    conn.commit()
    conn.close()
    logger.info(f"✅ Sertifikat yuborildi: #{request_id}")

def add_to_excel(req):
    try:
        with open(EXCEL_FILE, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                req['id'],
                req['user_id'],
                f"@{req['username']}" if req['username'] else '-',
                req['full_name'],
                req['guruh'],
                req['telefon'],
                req['telegram_username'],
                req['created_at'],
                req['approved_at'] or '-',
                req['certificate_sent_at'] or '-'
            ])
        logger.info(f"✅ Excel ga qo'shildi: #{req['id']}")
        return True
    except Exception as e:
        logger.error(f"❌ Excel ga qo'shishda xatolik: {e}")
        return False

async def setup_bot_commands():
    # Oddiy foydalanuvchilar uchun
    user_commands = [
        BotCommand(command="start", description="Sertifikat olish")
    ]
    await bot.set_my_commands(user_commands)
    
    # Admin uchun
    admin_commands = [
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="kutish", description="Kutayotgan so'rovlar"),
        BotCommand(command="statistika", description="Statistika"),
        BotCommand(command="tasdiqlash", description="So'rovni tasdiqlash"),
        BotCommand(command="rad", description="So'rovni rad etish"),
        BotCommand(command="yuborish", description="Sertifikat yuborish"),
        BotCommand(command="xabar", description="Foydalanuvchiga xabar"),
        BotCommand(command="export", description="Excel yuklab olish")
    ]
    await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
    logger.info("✅ Bot komandalar menyusi sozlandi")

@dp.message(Command("start"))
async def start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(START_MESSAGE)
    await asyncio.sleep(1)
    await msg.answer(
        "Davom etish uchun tugmani bosing 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Sertifikat olish", callback_data="start_cert")]
        ])
    )

@dp.callback_query(F.data == "start_cert")
async def start_cert(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(WARNING_MESSAGE)
    await asyncio.sleep(1)
    await cb.message.answer(
        "⚠️ Ogohlantirishni o'qib chiqdingizmi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Roziman, davom etaman", callback_data="accept_warning")],
            [InlineKeyboardButton(text="❌ Chiqish", callback_data="exit_bot")]
        ])
    )

@dp.callback_query(F.data == "exit_bot")
async def exit_bot(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer("❌ Siz botdan chiqib ketdingiz.\n\nQayta boshlash uchun /start ni bosing")
    await state.clear()

@dp.callback_query(F.data == "accept_warning")
async def accept_warning(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(CONGRATS_MESSAGE)
    await asyncio.sleep(1)
    await cb.message.answer(
        "Tayyor bo'lsangiz boshlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Davom etish", callback_data="continue_cert")]
        ])
    )

@dp.callback_query(F.data == "continue_cert")
async def continue_cert(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    
    # Dublikat tekshirish
    duplicate = check_duplicate_user(cb.from_user.id)
    if duplicate:
        duplicate_id, duplicate_status, duplicate_date = duplicate
        
        status_text = {
            'pending': '⏳ Kutishda',
            'approved': '✅ Tasdiqlangan',
            'rejected': '❌ Rad etilgan'
        }.get(duplicate_status, duplicate_status)
        
        await cb.message.answer(
            f"""❌ <b>Siz allaqachon ariza yuborgansiz!</b>

📋 <b>So'rov #{duplicate_id}</b>
📊 <b>Status:</b> {status_text}
📅 <b>Yuborilgan:</b> {duplicate_date}

⏳ Iltimos, admin javobini kuting!

Muammo bo'lsa, admin bilan bog'laning."""
        )
        return
    
    await state.update_data(user_id=cb.from_user.id, username=cb.from_user.username)
    await cb.message.answer(
        """<b>1️⃣ ISM va FAMILIYANGIZNI kiriting</b>

⚠️ <b>DIQQAT!</b> Sertifikatda aynan shu ko'rinishda chop etiladi!

✅ <b>To'g'ri yozing:</b>
• Lotin harflarida
• <b>Bosh harflar Katta harfda bo'lishi kerak!</b>"""
    )
    await state.set_state(RegistrationStates.waiting_full_name)

@dp.message(RegistrationStates.waiting_full_name)
async def get_full_name(msg: Message, state: FSMContext):
    full_name = msg.text.strip()
    
    # Oddiy tekshirish
    if len(full_name) < 5:
        await msg.answer("❌ Ism va Familiya juda qisqa! Qaytadan kiriting:")
        return
    
    await state.update_data(full_name=full_name)
    await msg.answer("✅ <b>Qabul qilindi!</b>")
    await asyncio.sleep(0.5)
    
    await msg.answer(
        """<b>2️⃣ Quyidagi ma'lumotlarni yuboring:</b>

▫️ Qaysi guruhda o'qigansiz (to'liq nom)
▫️ Telefon raqami
▫️ Telegram username

⚠️ <b>Aynan shu tartibda yozing!</b>

<b>Masalan:</b>

<code>Standart-Premium 00.00.0000 guruh
+998901234567
@username</code>

<b>Barcha ma'lumotlarni BITTA XABARDA yuboring!</b>"""
    )
    await state.set_state(RegistrationStates.waiting_details)

@dp.message(RegistrationStates.waiting_details)
async def get_details(msg: Message, state: FSMContext):
    lines = msg.text.strip().split('\n')
    
    if len(lines) < 3:
        await msg.answer(
            """❌ <b>Noto'g'ri format!</b>

Iltimos, to'g'ri formatda yuboring:

<code>Standart-Premium 00.00.0000 guruh
+998901234567
@username</code>

(Har bir ma'lumot alohida qatorda)"""
        )
        return
    
    guruh = lines[0].strip()
    telefon = lines[1].strip()
    telegram_username = lines[2].strip().replace('@', '')
    
    await state.update_data(
        guruh=guruh,
        telefon=telefon,
        telegram_username=telegram_username
    )
    
    data = await state.get_data()
    
    await msg.answer(
        f"""📋 <b>MA'LUMOTLARINGIZNI TEKSHIRING:</b>

👤 <b>Ism-Familiya:</b> {data['full_name']}
👥 <b>Guruh:</b> {guruh}
📱 <b>Telefon:</b> {telefon}
📱 <b>Telegram:</b> @{telegram_username}

⚠️ <b>To'g'rimi?</b>""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, to'g'ri", callback_data="confirm_yes"),
                InlineKeyboardButton(text="❌ Qaytadan", callback_data="confirm_no")
            ]
        ])
    )
    await state.set_state(RegistrationStates.waiting_confirmation)

@dp.callback_query(F.data == "confirm_no", RegistrationStates.waiting_confirmation)
async def confirm_no(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer("❌ Bekor qilindi. Qaytadan boshlash uchun /start ni bosing")
    await state.clear()

@dp.callback_query(F.data == "confirm_yes", RegistrationStates.waiting_confirmation)
async def confirm_yes(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    
    data = await state.get_data()
    request_id = save_request(data)
    
    await cb.message.answer(
        f"""✅ <b>Arizangiz yuborildi!</b>

📋 <b>So'rov #{request_id}</b>

Admin tekshirmoqda... ⏳

Sertifikatingiz tayyorlangach, bu yerga yuboriladi! 📜"""
    )
    
    # Telefon dublikat tekshirish
    duplicate_phone = check_duplicate_phone(data['telefon'], request_id)
    
    duplicate_warning = ""
    if duplicate_phone:
        dup_id, dup_name, dup_status, dup_date = duplicate_phone
        duplicate_warning = f"""

⚠️ <b>DIQQAT! Telefon raqam dublikat!</b>

Bu telefon raqam avval ishlatilgan:
📋 So'rov #{dup_id} - {dup_name}
📊 Status: {dup_status}
📅 Sana: {dup_date}"""
    
    # Adminga yuborish
    await bot.send_message(
        ADMIN_ID,
        f"""🆕 <b>YANGI SERTIFIKAT SO'ROVI #{request_id}</b>

👤 <b>Ism-Familiya:</b> {data['full_name']}
👥 <b>Guruh:</b> {data['guruh']}
📱 <b>Telefon:</b> {data['telefon']}
📱 <b>Telegram:</b> @{data['telegram_username']}
📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

🆔 <b>User ID:</b> {data['user_id']}
👤 <b>Username:</b> @{data['username'] or '-'}{duplicate_warning}""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{request_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{request_id}")
            ]
        ])
    )
    
    await state.clear()

# ADMIN COMMANDS

@dp.message(Command("kutish"))
async def pending(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute("""SELECT id, full_name, guruh, created_at 
                 FROM certificate_requests 
                 WHERE status='pending' 
                 ORDER BY created_at DESC""")
    requests = c.fetchall()
    conn.close()
    
    if not requests:
        await msg.answer("📭 <b>Kutayotgan so'rovlar yo'q</b>")
        return
    
    txt = "📋 <b>KUTAYOTGAN SO'ROVLAR:</b>\n\n"
    for req in requests:
        txt += f"<b>#{req[0]}</b> - {req[1]}\n👥 {req[2]}\n📅 {req[3]}\n\n"
    await msg.answer(txt)

@dp.message(Command("statistika"))
async def stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM certificate_requests")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM certificate_requests WHERE status='pending'")
    pend = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM certificate_requests WHERE status='approved'")
    appr = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM certificate_requests WHERE status='rejected'")
    rej = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM certificate_requests WHERE certificate_sent_at IS NOT NULL")
    sent = c.fetchone()[0]
    conn.close()
    
    await msg.answer(
        f"""📊 <b>STATISTIKA</b>

📋 Jami so'rovlar: {total}
⏳ Kutishda: {pend}
✅ Tasdiqlangan: {appr}
❌ Rad etilgan: {rej}
📤 Sertifikat yuborilgan: {sent}"""
    )

@dp.message(Command("export"))
async def export(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    
    if not os.path.exists(EXCEL_FILE):
        await msg.answer("📭 <b>Excel fayl mavjud emas</b>")
        return
    
    with open(EXCEL_FILE, 'r', encoding='utf-8-sig') as f:
        row_count = sum(1 for _ in f) - 1
    
    await msg.answer_document(
        FSInputFile(EXCEL_FILE), 
        caption=f"📊 <b>TASDIQLANGAN SERTIFIKATLAR</b>\n\n✅ Jami: {row_count} ta"
    )

@dp.message(Command("xabar"))
async def send_message_cmd(msg: Message, state: FSMContext):
    """Foydalanuvchiga xabar yuborish"""
    if msg.from_user.id != ADMIN_ID:
        return
    
    try:
        # /xabar 15 formatida bo'lsa
        request_id = int(msg.text.split()[1])
        req = get_request(request_id)
        
        if not req:
            await msg.answer("❌ <b>So'rov topilmadi!</b>")
            return
        
        await state.update_data(message_target_id=request_id)
        await state.set_state(AdminStates.waiting_message_text)
        
        await msg.answer(
            f"""💬 <b>XABAR YUBORISH</b>

✅ So'rov #{request_id} topildi

👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}
📱 <b>Telefon:</b> {req['telefon']}
📱 <b>Telegram:</b> @{req['telegram_username']}

Xabaringizni yozing:"""
        )
        
    except (IndexError, ValueError):
        # /xabar deb yozilsa
        await msg.answer(
            """💬 <b>XABAR YUBORISH</b>

So'rov raqamini kiriting:

<b>Masalan:</b> <code>15</code>"""
        )
        await state.set_state(AdminStates.waiting_message_id)

@dp.message(AdminStates.waiting_message_id)
async def get_message_id(msg: Message, state: FSMContext):
    """So'rov ID sini olish"""
    if msg.from_user.id != ADMIN_ID:
        return
    
    try:
        request_id = int(msg.text.strip())
        req = get_request(request_id)
        
        if not req:
            await msg.answer("❌ <b>So'rov topilmadi!</b>\n\nQayta urinib ko'ring:")
            return
        
        await state.update_data(message_target_id=request_id)
        await state.set_state(AdminStates.waiting_message_text)
        
        await msg.answer(
            f"""✅ <b>So'rov #{request_id} topildi</b>

👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}
📱 <b>Telefon:</b> {req['telefon']}
📱 <b>Telegram:</b> @{req['telegram_username']}

Xabaringizni yozing:"""
        )
        
    except ValueError:
        await msg.answer("❌ <b>Faqat raqam kiriting!</b>\n\nMasalan: <code>15</code>")

@dp.message(AdminStates.waiting_message_text)
async def get_message_text(msg: Message, state: FSMContext):
    """Xabar matnini olish va yuborish"""
    if msg.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    request_id = data['message_target_id']
    req = get_request(request_id)
    
    message_text = msg.text
    
    try:
        # Foydalanuvchiga xabar yuborish
        await bot.send_message(
            req['user_id'],
            f"""📩 <b>ADMIN XABARI:</b>

{message_text}"""
        )
        
        await msg.answer(
            f"""✅ <b>Xabar yuborildi!</b>

👤 <b>Ism:</b> {req['full_name']}
📋 <b>So'rov:</b> #{request_id}
📩 <b>Xabar:</b> "{message_text[:50]}{'...' if len(message_text) > 50 else ''}"
"""
        )
        
    except Exception as e:
        await msg.answer(f"❌ <b>Xatolik:</b> {e}")
    
    await state.clear()

def check_duplicate_user(user_id):
    """Foydalanuvchi avval ariza yuborgan-yubormaganini tekshirish"""
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    c.execute("SELECT id, status, created_at FROM certificate_requests WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def check_duplicate_phone(telefon, exclude_id=None):
    """Telefon raqam avval ishlatilgan-ishlatilmaganini tekshirish"""
    conn = sqlite3.connect('certificate_database.db')
    c = conn.cursor()
    if exclude_id:
        c.execute("""SELECT id, full_name, status, created_at 
                     FROM certificate_requests 
                     WHERE telefon=? AND id!=? 
                     ORDER BY created_at DESC LIMIT 1""", (telefon, exclude_id))
    else:
        c.execute("""SELECT id, full_name, status, created_at 
                     FROM certificate_requests 
                     WHERE telefon=? 
                     ORDER BY created_at DESC LIMIT 1""", (telefon,))
    result = c.fetchone()
    conn.close()
    return result

@dp.callback_query(F.data.startswith("approve_"))
async def approve_btn(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID:
        return
    
    request_id = int(cb.data.split("_")[1])
    req = get_request(request_id)
    
    if not req or req['status'] != 'pending':
        await cb.answer("⚠️ So'rov allaqachon ko'rib chiqilgan", show_alert=True)
        return
    
    update_status(request_id, 'approved')
    
    await cb.message.edit_text(
        cb.message.text + "\n\n✅ <b>TASDIQLANDI</b>"
    )
    await cb.answer("✅ Tasdiqlandi", show_alert=False)
    
    await bot.send_message(
        ADMIN_ID,
        f"""✅ <b>So'rov #{request_id} tasdiqlandi</b>

Endi Photoshop'da sertifikat yasang va yuboring:

<b>Komanda:</b> <code>/yuborish {request_id}</code>

yoki quyidagi tugmani bosing:""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Sertifikat yuborish", callback_data=f"send_{request_id}")]
        ])
    )

@dp.callback_query(F.data.startswith("reject_"))
async def reject_btn(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        return
    
    request_id = int(cb.data.split("_")[1])
    req = get_request(request_id)
    
    if not req or req['status'] != 'pending':
        await cb.answer("⚠️ So'rov allaqachon ko'rib chiqilgan", show_alert=True)
        return
    
    update_status(request_id, 'rejected')
    
    try:
        await bot.send_message(
            req['user_id'],
            f"❌ <b>So'rov #{request_id} rad etildi</b>\n\nQo'shimcha ma'lumot uchun admin bilan bog'laning."
        )
    except:
        pass
    
    await cb.message.edit_text(
        cb.message.text + "\n\n❌ <b>RAD ETILDI</b>"
    )
    await cb.answer("✅ Rad etildi", show_alert=False)

@dp.callback_query(F.data.startswith("send_"))
async def send_btn(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID:
        return
    
    request_id = int(cb.data.split("_")[1])
    req = get_request(request_id)
    
    if not req:
        await cb.answer("❌ So'rov topilmadi", show_alert=True)
        return
    
    if req['status'] != 'approved':
        await cb.answer("⚠️ So'rov hali tasdiqlanmagan!", show_alert=True)
        return
    
    await state.update_data(current_request_id=request_id)
    await state.set_state(AdminStates.waiting_certificate_photo)
    
    await cb.message.answer(
        f"""📤 <b>So'rov #{request_id} uchun sertifikat yuboring</b>

👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}

Sertifikat PNG yoki JPG formatda yuboring:"""
    )

@dp.message(Command("yuborish"))
async def send_cmd(msg: Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return
    
    try:
        request_id = int(msg.text.split()[1])
    except:
        await msg.answer("❌ <b>Noto'g'ri format!</b>\n\nTo'g'ri: <code>/yuborish 1</code>")
        return
    
    req = get_request(request_id)
    
    if not req:
        await msg.answer("❌ <b>So'rov topilmadi!</b>")
        return
    
    if req['status'] != 'approved':
        await msg.answer("⚠️ <b>So'rov hali tasdiqlanmagan!</b>")
        return
    
    await state.update_data(current_request_id=request_id)
    await state.set_state(AdminStates.waiting_certificate_photo)
    
    await msg.answer(
        f"""📤 <b>So'rov #{request_id} uchun sertifikat yuboring</b>

👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}

Sertifikat PNG yoki JPG formatda yuboring:"""
    )

@dp.message(AdminStates.waiting_certificate_photo, F.photo)
async def receive_certificate_photo(msg: Message, state: FSMContext):
    """Sertifikat RASM sifatida yuborilganda"""
    if msg.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    request_id = data['current_request_id']
    req = get_request(request_id)
    
    photo_id = msg.photo[-1].file_id
    
    await state.update_data(certificate_photo_id=photo_id)
    
    await msg.answer(
        f"""✅ <b>Sertifikat qabul qilindi!</b>

👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}

Foydalanuvchiga yuborilsinmi?""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📤 Yuborish", callback_data=f"confirm_send_{request_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_send")
            ]
        ])
    )
    await state.set_state(AdminStates.waiting_send_confirmation)

@dp.message(AdminStates.waiting_certificate_photo, F.document)
async def receive_certificate_document(msg: Message, state: FSMContext):
    """Sertifikat FAYL sifatida yuborilganda"""
    if msg.from_user.id != ADMIN_ID:
        return
    
    # Faqat rasm fayllarini qabul qilish
    if msg.document.mime_type not in ['image/png', 'image/jpeg', 'image/jpg']:
        await msg.answer("❌ <b>Faqat PNG yoki JPG formatdagi rasm yuborishingiz mumkin!</b>")
        return
    
    data = await state.get_data()
    request_id = data['current_request_id']
    req = get_request(request_id)
    
    # Document file_id ni ishlatish
    photo_id = msg.document.file_id
    
    await state.update_data(certificate_photo_id=photo_id, is_document=True)
    
    await msg.answer(
        f"""✅ <b>Sertifikat qabul qilindi!</b>

👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}

Foydalanuvchiga yuborilsinmi?""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📤 Yuborish", callback_data=f"confirm_send_{request_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_send")
            ]
        ])
    )
    await state.set_state(AdminStates.waiting_send_confirmation)

@dp.callback_query(F.data == "cancel_send", AdminStates.waiting_send_confirmation)
async def cancel_send(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer("❌ <b>Bekor qilindi</b>")
    await state.clear()

@dp.callback_query(F.data.startswith("confirm_send_"), AdminStates.waiting_send_confirmation)
async def confirm_send(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID:
        return
    
    request_id = int(cb.data.split("_")[2])
    req = get_request(request_id)
    data = await state.get_data()
    photo_id = data['certificate_photo_id']
    is_document = data.get('is_document', False)
    
    try:
        # Foydalanuvchiga yuborish (photo yoki document)
        if is_document:
            # Fayl sifatida yuborilgan bo'lsa
            await bot.send_document(
                req['user_id'],
                photo_id,
                caption=CERTIFICATE_SUCCESS_MESSAGE
            )
        else:
            # Rasm sifatida yuborilgan bo'lsa
            await bot.send_photo(
                req['user_id'],
                photo_id,
                caption=CERTIFICATE_SUCCESS_MESSAGE
            )
        
        # Sertifikat yuborildi deb belgilash
        mark_certificate_sent(request_id)
        
        # Excel ga qo'shish
        add_to_excel(req)
        
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(
            f"""✅ <b>Sertifikat yuborildi!</b>

📋 <b>So'rov #{request_id}</b>
👤 <b>Ism:</b> {req['full_name']}
👥 <b>Guruh:</b> {req['guruh']}
📤 <b>Yuborildi:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
📊 <b>Excel ga qo'shildi:</b> ✅"""
        )
        
    except Exception as e:
        await cb.message.answer(
            f"""❌ <b>XATOLIK! Sertifikat yuborilmadi!</b>

<b>Sabab:</b> {str(e)}

<b>Ehtimoliy sabablar:</b>
• Foydalanuvchi botni bloklagan
• Foydalanuvchi Telegram'ni o'chirgan
• User ID noto'g'ri

<b>Foydalanuvchi ma'lumotlari:</b>
👤 User ID: {req['user_id']}
👤 Username: @{req.get('username', '-')}
📱 Telegram: @{req['telegram_username']}"""
        )
    
    await state.clear()

async def main():
    init_db()
    init_excel()
    await setup_bot_commands()
    logger.info("🤖 Sertifikat Bot ishga tushdi!")
    logger.info(f"📊 Excel fayl: {EXCEL_FILE}")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # HTTP server for Render.com (keeps port open)
    from aiohttp import web
    
    async def health_check(request):
        return web.Response(text="Bot is running!")
    
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render uses PORT environment variable
    port = int(os.getenv('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🌐 HTTP server running on port {port}")
    
    # Start bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Bot to'xtatildi")
