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
    await sen
