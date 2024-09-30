#!./.venv/bin/python

import io
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

from open_ai import (
    ai_describe_image,
    ai_retell,
    ai_identify_parameters,
    ai_retell,
    ai_summarize,
    ai_transcript_audio,
)
import base64

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_description = await process_images(update, context)
    fb_save_message(update.message, image_description)


async def process_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    image_description = None
    if update.message.photo != None and len(update.message.photo) > 0:
        highest_quality_photo_id = update.message.photo[-1].file_id

        file = await context.bot.get_file(highest_quality_photo_id)
        byte_array = await file.download_as_bytearray()
        image_data = base64.b64encode(byte_array).decode("utf-8")
        image_description = ai_describe_image(image_data)
    return image_description

async def default_summarize(
    update: Update, context: ContextTypes.DEFAULT_TYPE, ai_func: Callable
):
    try:
        limit = (
            int(context.args[0])
            if (len(context.args) > 0 and context.args[0] is not None)
            else int(os.getenv("DEFAULT_HISTORY_LENGTH"))
        )
        params = {}

        params["history_length"] = limit
        params["language"] = os.getenv("DEFAULT_LANGUAGE")
        params["tone"] = os.getenv("DEFAULT_TONE")
        params["chat_id"] = str(update.message.chat.id)

        messages = get_last_messages(str(update.message.chat.id), limit)
        result = ai_func(messages, params, update.message.chat.type)
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


async def retell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await default_summarize(update, context, ai_retell)


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Chat id: " + str(update.message.chat.id)
    )


async def bot_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        params = ai_identify_parameters(update.message.text)

        if params["history_length"] is None:
            params["history_length"] = int(os.getenv("DEFAULT_HISTORY_LENGTH"))
        if params["language"] is None:
            params["language"] = os.getenv("DEFAULT_LANGUAGE")
        if params["tone"] is None:
            params["tone"] = os.getenv("DEFAULT_TONE")

        params["chat_id"] = str(update.message.chat.id)

        messages = get_last_messages(
            str(update.message.chat.id), params["history_length"]
        )
        result = ai_retell(messages, params)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=escape(result),
            parse_mode="MarkdownV2",
        )
    except Exception as error:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=repr(error)
        )

async def process_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_file = await context.bot.get_file(update.message.voice.file_id)
    path_to_file = await new_file.download_to_drive()
    transcription = ai_transcript_audio(path_to_file)
    fb_save_message(update.message, transcription)
    path_to_file.unlink()

def start_bot():
    bot_name = os.getenv("TELEGRAM_BOT_NAME")

    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    start_handler = CommandHandler("start", start)
    s_handler = CommandHandler("s", summarize)
    summarize_handler = CommandHandler("summarize", summarize)
    chat_id_handler = CommandHandler("chatid", get_chat_id)
    mention_handler = MessageHandler(filters.Mention(bot_name), bot_mention)
    voice_message_handler = MessageHandler(filters.VOICE, process_voice_message)
    save_message_handler = MessageHandler(
        (filters.TEXT | filters.PHOTO)
        & (~filters.COMMAND)
        & (~filters.Mention(bot_name)),
        save_message,
    )

    application.add_handler(start_handler)
    application.add_handler(s_handler)
    application.add_handler(summarize_handler)
    application.add_handler(save_message_handler)
    application.add_handler(chat_id_handler)
    application.add_handler(mention_handler)
    application.add_handler(voice_message_handler)

    application.run_polling()
