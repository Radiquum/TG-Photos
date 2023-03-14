import os
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes
from modules.database import search_tags_in_db
from modules.bot_get_media import search_list, search_image
from telegram.ext import CommandHandler
from telegram.ext import filters
from telegram.ext import MessageHandler
from modules.database import update_db_initiate
import datetime
current_time = datetime.datetime.now().strftime("%b%d%Y-%I%M%S%p")


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def get_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tags = search_tags_in_db()
    if not tags:
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
    

async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await context.bot.sendDocument(chat_id=update.effective_chat.id, document=f'logs/log-{current_time}.log')


async def command_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Unknown command or Not authorized user."
    )

start_handler = CommandHandler("start", command_start, filters.Chat(username=os.getenv("username")))
search_handler = CommandHandler("search", search_image, filters.Chat(username=os.getenv("username")))
searchList_handler = CommandHandler("searchList", search_list, filters.Chat(username=os.getenv("username")))
tagList_handler = CommandHandler("tagList", get_tags, filters.Chat(username=os.getenv("username")))
update_handler = CommandHandler("update", update_db_initiate, filters.Chat(username=os.getenv("username")))
log_handler = CommandHandler("log", get_log, filters.Chat(username=os.getenv("username")))
unknown_handler = MessageHandler(filters.COMMAND, command_unknown)
