import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import asyncio
import os

TOKEN = "7967415879:AAH4n39ijxskeYDcLU7Yw3jf3oJG-J-QTx4"

VOTE_MESSAGE = "⚽️ Football on Wednesday at 20:00!\nAre you coming? Press ➕ or ➖"

voters = set()
chat_id = None
vote_message_id = None

logging.basicConfig(level=logging.INFO)

async def send_vote_message(app):
    global vote_message_id
    if chat_id:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Coming", callback_data="yes"),
             InlineKeyboardButton("➖ Not coming", callback_data="no")]
        ])
        message = await app.bot.send_message(chat_id=chat_id, text=VOTE_MESSAGE, reply_markup=keyboard)
        vote_message_id = message.message_id

async def update_vote_message(context: ContextTypes.DEFAULT_TYPE):
    if chat_id and vote_message_id:
        text = VOTE_MESSAGE + "\n\n" + "\n".join(f"• {name}" for name in voters) if voters else VOTE_MESSAGE + "\n\n(no one yet)"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Coming", callback_data="yes"),
             InlineKeyboardButton("➖ Not coming", callback_data="no")]
        ])
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=vote_message_id, text=text, reply_markup=keyboard)
        except Exception as e:
            logging.error(f"Failed to update message: {e}")

async def start_vote(context: ContextTypes.DEFAULT_TYPE):
    await send_vote_message(context.application)

async def stop_vote(context: ContextTypes.DEFAULT_TYPE):
    global voters
    voters.clear()
    await context.bot.send_message(chat_id=chat_id, text="📭 Voting is now closed. The list has been cleared.")

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
    await update.message.reply_text("✅ This chat has been saved. The bot will post votes here.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("setchat", set_chat))
    app.add_handler(CallbackQueryHandler(button_handler))

    scheduler = BackgroundScheduler(timezone="Asia/Baku")
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(start_vote(app), app.loop), 'cron', hour=10, minute=23)
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(stop_vote(app), app.loop), 'cron', day_of_week='wed', hour=20)
    scheduler.start()

    app.run_polling()

if __name__ == '__main__':
    main()
