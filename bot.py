import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import asyncio
import os
from pytz import timezone

# Token
TOKEN = "7967415879:AAH4n39ijxskeYDcLU7Yw3jf3oJG-J-QTx4"

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

async def send_vote_message(context: ContextTypes.DEFAULT_TYPE, with_reminder: bool = False):
    if chat_id:
        if with_reminder:
            await context.bot.send_message(chat_id=chat_id, text="📢 Salam! DOST Futbol üçün qeydiyyat başladı. Kim gəlir? `+` yaz, çıxırsansa `-` yaz! ⚽️")
        await context.bot.send_message(chat_id=chat_id, text=format_list())
        logger.info("[send_vote_message] Sent vote list")

def clear_voters():
    global voters
    voters.clear()
    logger.info("[clear_voters] Voter list cleared")

async def start_vote(context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"[start_vote] Triggered at {datetime.now(timezone('Asia/Baku'))}")
    if not chat_id:
        logger.warning("[start_vote] Chat ID is not set, aborting vote start")
        return
    clear_voters()
    await send_vote_message(context, with_reminder=True)

async def stop_vote(context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"[stop_vote] Triggered at {datetime.now(timezone('Asia/Baku'))}")
    if chat_id:
        clear_voters()
        await context.bot.send_message(chat_id=chat_id, text="🛑 Səsvermə bağlandı. Siyahı sıfırlandı.")
        logger.info("[stop_vote] Voting closed and list cleared")

async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global voters
    if not chat_id or update.effective_chat.id != chat_id:
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

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("setchat", set_chat))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vote))

    logger.info(f"🕒 Bot running at: {datetime.now(timezone('Asia/Baku'))}")

    scheduler = BackgroundScheduler(timezone=timezone("Asia/Baku"))

    # 🟢 Wednesday 11:45 – Start voting
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(start_vote(app), app.loop),
                      'cron', day_of_week='wed', hour=11, minute=45)

    # 🔴 Wednesday 11:46 – Stop voting
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(stop_vote(app), app.loop),
                      'cron', day_of_week='wed', hour=11, minute=46)

    scheduler.start()
    logger.info("✅ Scheduler started (Asia/Baku)")
    app.run_polling()

if __name__ == "__main__":
    main()
