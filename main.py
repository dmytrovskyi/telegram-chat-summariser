import logging
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
)
from firebase import save_message as fb_save_message, get_last_messages

import os
from dotenv import load_dotenv

from open_ai import ai_summarize

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fb_save_message(update.message)


async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limit = int(context.args[0]) if context.args[0] is not None else 50
    messages = get_last_messages(limit)
    result = ai_summarize(messages)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)


application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

start_handler = CommandHandler("start", start)
summarize_handler = CommandHandler("summarize", summarize)
save_message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), save_message)

application.add_handler(start_handler)
application.add_handler(summarize_handler)
application.add_handler(save_message_handler)

application.run_polling()
