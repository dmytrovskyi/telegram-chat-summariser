#!./.venv/bin/python

import logging
from typing import Callable
from telegram import Update
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

from open_ai import ai_identify_parameters, ai_summarize, ai_summarize_ironic

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
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=result, parse_mode="MarkdownV2"
        )
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


async def bot_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        params = ai_identify_parameters(update.message.text)

        if params["history_length"] is None:
            params["history_length"] = 100
        if params["language"] is None:
            params["language"] = "UKRAINIAN"
        if params["tone"] is None:
            params["tone"] = "NEUTRAL"

        messages = get_last_messages(
            str(update.message.chat.id), params["history_length"]
        )
        result = ai_summarize(messages, params)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=escape(result),
            parse_mode="MarkdownV2",
        )
    except Exception as error:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=repr(error)
        )
        
def main():
    bot_name = os.getenv("TELEGRAM_BOT_NAME")

    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    start_handler = CommandHandler("start", start)
    summarize_handler = CommandHandler("summarize", summarize)
    summarize_handler = CommandHandler("s", summarize)
    ironic_handler = CommandHandler("ironic", summarize_ironic)
    chat_id_handler = CommandHandler("chatid", get_chat_id)
    mention_handler = MessageHandler(filters.Mention(bot_name), bot_mention)
    save_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND) & (~filters.Mention(bot_name)),
        save_message,
    )

    application.add_handler(start_handler)
    application.add_handler(summarize_handler)
    application.add_handler(ironic_handler)
    application.add_handler(save_message_handler)
    application.add_handler(chat_id_handler)
    application.add_handler(mention_handler)

    application.run_polling()

if __name__ == "__main__":
    main()