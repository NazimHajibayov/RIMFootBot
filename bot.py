import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler
)
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import asyncio
import os

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Get token from env
TOKEN = "7967415879:AAH4n39ijxskeYDcLU7Yw3jf3oJG-J-QTx4"

# Message text
VOTE_MESSAGE = "⚽️ Football on Wednesday at 20:00!\nAre you coming? Press ➕ or ➖"

# State variables
voters = set()
chat_id = None
vote_message_id = None

# Sends the vote message
async def send_vote_message(app):
    global vote_message_id
    if chat_id:
        logging.info("Sending vote message to chat_id: %s", chat_id)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Coming", callback_data="yes"),
            InlineKeyboardButton("➖ Not coming", callback_data="no")
        ]])
        message = await app.bot.send_message(chat_id=chat_id, text=VOTE_MESSAGE, reply_markup=keyboard)
        vote_message_id = message.message_id

# Clears the voter list
def clear_voters():
    logging.info("Clearing voters list")
    global voters
    voters.clear()

# Updates the vote message with current voter list
async def update_vote_message(context: ContextTypes.DEFAULT_TYPE):
    if chat_id and vote_message_id:
        logging.info("Updating vote message")
        text = VOTE_MESSAGE + "\n\n" + "\n".join(f"• {name}" for name in voters) if voters else VOTE_MESSAGE + "\n\n📝 No one has voted yet."
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Coming", callback_data="yes"),
            InlineKeyboardButton("➖ Not coming", callback_data="no")
        ]])
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=vote_message_id, text=text, reply_markup=keyboard)
        except Exception as e:
            logging.error(f"Failed to update message: {e}")

# Schedules start vote
async def start_vote(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Starting vote...")
    await send_vote_message(context.application)

# Schedules stop vote
async def stop_vote(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Stopping vote...")
    clear_voters()
    await context.bot.send_message(chat_id=chat_id, text="📭 Voting closed. The list has been cleared.")

# Callback handler for buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.from_user.full_name
    logging.info(f"Button clicked: {query.data} by {name}")
    if query.data == "yes":
        voters.add(name)
    elif query.data == "no" and name in voters:
        voters.remove(name)
    await update_vote_message(context)

# /setchat to define chat_id
async def set_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id
    logging.info(f"Chat ID set to: {chat_id}")
    await update.message.reply_text("✅ This chat has been saved. The bot will post votes here.")

# /list command to show current list
async def list_voters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if voters:
        text = "📝 Current players:\n" + "\n".join(f"• {name}" for name in voters)
    else:
        text = "📝 No one has voted yet."
    await update.message.reply_text(text)

# /startvote to trigger manually
async def manual_start_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_vote(context)

# App entry
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("setchat", set_chat))
    app.add_handler(CommandHandler("list", list_voters))
    app.add_handler(CommandHandler("startvote", manual_start_vote))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Scheduler jobs
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(start_vote(app), app.loop), 'cron', day_of_week='mon', hour=20)
    scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(stop_vote(app), app.loop), 'cron', day_of_week='wed', hour=20)
    scheduler.start()

    logging.info("Bot started.")
    app.run_polling()

if __name__ == '__main__':
    main()
