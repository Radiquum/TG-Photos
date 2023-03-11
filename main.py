import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import filters
from telegram.ext import MessageHandler

load_dotenv()
botToken = os.getenv("botToken")
chatId = os.getenv("chatId")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from modules.database import (
    update_DB_initiate,
    search_tags_in_DB,
)

from modules.bot_login import login_handler
from modules.bot_upload import upload_handler
from modules.bot_post_actions import remove, edit_handler
from modules.bot_get_media import (
    search_image,
    search_list,
    get_list_media,
    search_image_navigation,
    search_list_navigation,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def get_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tags = search_tags_in_DB()
    if tags == []:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id,
            text="Tags not found.",
        )
        return False

    keyboard = [
        [InlineKeyboardButton(tag, callback_data=f"/searchlist {tag}")] for tag in tags
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot_data["msgId"] = await context.bot.sendMessage(
        chat_id=update.effective_chat.id,
        text="available tags.",
        reply_markup=reply_markup,
        reply_to_message_id=update.effective_message.id,
    )


async def callback_commands_handler(update, context):
    callback = update.callback_query.data
    if callback[:11] == "/searchlist":
        context.args = ["tag", callback[12:].strip()]
        await search_list(update, context)
    if callback == "dummy":
        return


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Unknown command or Not authorized user."
    )


if __name__ == "__main__":
    start_handler = CommandHandler(
        "start", start, filters.Chat(username=os.getenv("username"))
    )
    searchList_handler = CommandHandler(
        "searchList", search_list, filters.Chat(username=os.getenv("username"))
    )
    search_handler = CommandHandler(
        "search", search_image, filters.Chat(username=os.getenv("username"))
    )
    tagList_handler = CommandHandler(
        "tagList", get_tags, filters.Chat(username=os.getenv("username"))
    )
    update_handler = CommandHandler(
        "update", update_DB_initiate, filters.Chat(username=os.getenv("username"))
    )
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application = ApplicationBuilder().token(botToken).build()
    application.add_handler(start_handler)
    application.add_handler(searchList_handler)
    application.add_handler(tagList_handler)
    application.add_handler(search_handler)
    application.add_handler(update_handler)
    application.add_handler(
        CallbackQueryHandler(search_image_navigation, pattern="^img")
    )
    application.add_handler(
        CallbackQueryHandler(search_list_navigation, pattern="^list")
    )
    application.add_handler(CallbackQueryHandler(get_list_media, pattern="^filename"))
    application.add_handler(CallbackQueryHandler(remove, pattern="^remove"))

    application.add_handler(
        CallbackQueryHandler(callback_commands_handler, pattern="^/")
    )
    application.add_handler(
        CallbackQueryHandler(callback_commands_handler, pattern="^dummy$")
    )

    application.add_handler(upload_handler)
    application.add_handler(login_handler)
    application.add_handler(edit_handler)

    application.add_handler(unknown_handler)
    application.run_polling()
