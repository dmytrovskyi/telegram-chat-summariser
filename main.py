#!./.venv/bin/python

import logging
from typing import Callable
from telegram import Update
import telegram
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
)
from firebase import save_message as fb_save_message, get_last_messages
from md2tgmd import escape


import os
from dotenv import load_dotenv

from open_ai import ai_summarize, ai_summarize_ironic

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


async def default_summarize(
    update: Update, context: ContextTypes.DEFAULT_TYPE, ai_func: Callable
):
    try:
        limit = (
            int(context.args[0])
            if (len(context.args) > 0 and context.args[0] is not None)
            else 100
        )
        messages = get_last_messages(str(update.message.chat.id), limit)
        result = ai_func(messages)
        result = escape(result)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result, parse_mode="MarkdownV2")
    except Exception as error:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=repr(error)
        )


async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await default_summarize(update, context, ai_summarize)


async def summarize_ironic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await default_summarize(update, context, ai_summarize_ironic)


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Chat id: " + str(update.message.chat.id)
    )


application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

start_handler = CommandHandler("start", start)
summarize_handler = CommandHandler("summarize", summarize)
summarize_handler = CommandHandler("s", summarize)
ironic_handler = CommandHandler("ironic", summarize_ironic)
save_message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), save_message)
chat_id_handler = CommandHandler("chatid", get_chat_id)

application.add_handler(start_handler)
application.add_handler(summarize_handler)
application.add_handler(ironic_handler)
application.add_handler(save_message_handler)
application.add_handler(chat_id_handler)

application.run_polling()
