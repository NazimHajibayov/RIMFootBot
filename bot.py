import logging
import asyncio
import nest_asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pytz import timezone

# Token
TOKEN = "7967415879:AAGSPaSSFLZZZQPUdnMzOT_uKbLWp2Usk4Y"

# Globals
voters = []
chat_id = None

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Voting message
VOTE_HEADER = "DOST Football:\n3-cü gün 20:00 oyununa gələnlər. Siyahıya qoşulmaq üçün `+`, çıxmaq ücün isə `-` yazın:\n"

def format_list():
    if not voters:
        return VOTE_HEADER + "(hələ heç kim yazılmayıb)"
    return VOTE_HEADER + "\n".join([f"{i+1}. {name}" for i, name in enumerate(voters)])

def is_voting_open() -> bool:
    now = datetime.now(timezone("Asia/Baku"))
    weekday = now.weekday()  # Monday=0, Sunday=6

    if weekday == 0 and now.hour >= 10:
        return True
    elif 0 < weekday < 2:
        return True
    elif weekday == 2 and now.hour < 20:
        return True
    return False

async def send_vote_message(context: ContextTypes.DEFAULT_TYPE = None, with_reminder: bool = False):
    if chat_id:
        bot = Bot(token=TOKEN)
        if with_reminder:
            await bot.send_message(chat_id=chat_id, text="📢 Salam! DOST Futbol üçün qeydiyyat başladı. Kim gəlir? `+` yaz, çıxırsansa `-` yaz! ⚽️")
        await bot.send_message(chat_id=chat_id, text=format_list())
        logger.info("[send_vote_message] Sent vote list")

def clear_voters():
    global voters
    voters.clear()
    logger.info("[clear_voters] Voter list cleared")

async def start_vote(context: ContextTypes.DEFAULT_TYPE = None):
    logger.info(f"[start_vote] Triggered at {datetime.now(timezone('Asia/Baku'))}")
    if not chat_id:
        logger.warning("[start_vote] Chat ID is not set, aborting vote start")
        return
    clear_voters()
    await send_vote_message(with_reminder=True)

async def stop_vote(context: ContextTypes.DEFAULT_TYPE = None):
    logger.info(f"[stop_vote] Triggered at {datetime.now(timezone('Asia/Baku'))}")
    if chat_id:
        clear_voters()
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=chat_id, text="🛑 Səsvermə bağlandı. Siyahı sıfırlandı.")
        logger.info("[stop_vote] Voting closed and list cleared")

async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global voters
    if not chat_id or update.effective_chat.id != chat_id:
        return

    if not is_voting_open():
        logger.info(f"[handle_vote] Ignored vote outside allowed time: {update.message.text}")
        return

    name = update.message.from_user.full_name
    text = update.message.text.strip()

    if text == "+":
        if name not in voters:
            voters.append(name)
            logger.info(f"[handle_vote] + {name}")
            await send_vote_message(context)
    elif text == "-":
        if name in voters:
            voters.remove(name)
            logger.info(f"[handle_vote] - {name}")
            await send_vote_message(context)

async def set_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id
    logger.info(f"[set_chat] Chat ID saved: {chat_id}")
    await update.message.reply_text("✅ Bu chat yadda saxlanıldı. Bot bura səsverməni göndərəcək.")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_list())

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    await app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("setchat", set_chat))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vote))

    logger.info(f"🕒 Bot running at: {datetime.now(timezone('Asia/Baku'))}")

    scheduler = BackgroundScheduler(timezone=timezone("Asia/Baku"))
    loop = asyncio.get_running_loop()

    # 🟢 Monday 10:00 – Start voting
    scheduler.add_job(lambda: loop.create_task(start_vote()), 
                      'cron', day_of_week='mon', hour=10, minute=00)

    # 🔴 Wednesday 20:00 – Stop voting
    scheduler.add_job(lambda: loop.create_task(stop_vote()), 
                      'cron', day_of_week='wed', hour=20, minute=00)

    scheduler.start()
    logger.info("✅ Scheduler started (Asia/Baku)")

    await app.run_polling(allowed_updates=[])

# 🔁 Safe for Railway / Linux
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
