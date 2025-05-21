
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import asyncio
import os

TOKEN = os.getenv("TOKEN")
print("TOKEN =", TOKEN)

VOTE_MESSAGE = "⚽️ Футбол в среду в 20:00!\nКто идёт? Жми ➕ или ➖"

voters = set()
chat_id = None
vote_message_id = None

logging.basicConfig(level=logging.INFO)

async def send_vote_message(app):
    global vote_message_id
    if chat_id:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Иду", callback_data="yes"),
             InlineKeyboardButton("➖ Не иду", callback_data="no")]
        ])
        message = await app.bot.send_message(chat_id=chat_id, text=VOTE_MESSAGE, reply_markup=keyboard)
        vote_message_id = message.message_id

def clear_voters():
    global voters
    voters.clear()

async def update_vote_message(context: ContextTypes.DEFAULT_TYPE):
    if chat_id and vote_message_id:
        text = VOTE_MESSAGE + "\n\n" + "\n".join(f"• {name}" for name in voters) if voters else VOTE_MESSAGE + "\n\n(пока никто не записался)"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Иду", callback_data="yes"),
             InlineKeyboardButton("➖ Не иду", callback_data="no")]
        ])
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=vote_message_id, text=text, reply_markup=keyboard)
        except:
            pass

async def start_vote(context: ContextTypes.DEFAULT_TYPE):
    await send_vote_message(context.application)

async def stop_vote(context: ContextTypes.DEFAULT_TYPE):
    clear_voters()
    await context.bot.send_message(chat_id=chat_id, text="📭 Голосование закрыто. Список очищен.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.from_user.full_name
    if query.data == "yes":
        voters.add(name)
    elif query.data == "no" and name in voters:
        voters.remove(name)
    await update_vote_message(context)

async def set_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id
    await update.message.reply_text("✅ Чат сохранён. Теперь бот будет присылать сюда опрос.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("setchat", set_chat))
    app.add_handler(CallbackQueryHandler(button_handler))

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(start_vote(app), app.loop), 'cron', day_of_week='mon', hour=20)
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(stop_vote(app), app.loop), 'cron', day_of_week='wed', hour=20)
    scheduler.start()

    app.run_polling()

if __name__ == '__main__':
    main()
