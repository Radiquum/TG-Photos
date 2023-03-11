import contextlib
import os

from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.errors import BadRequest
from pyrogram.errors import SessionPasswordNeeded
from telegram import Update
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

api_id = os.getenv("appId")
api_hash = os.getenv("appHash")
load_dotenv()


def login_purge(context: ContextTypes.DEFAULT_TYPE):
    with contextlib.suppress(KeyError):
        del context.bot_data["user_phone"]
        del context.bot_data["user_confirmation"]
        del context.bot_data["user_confirmation_code"]
        del context.bot_data["user_password"]
        del context.bot_data["msgId"]


PHONE, CONFIRMATION, PASSWORD = range(3)


async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with contextlib.suppress(FileNotFoundError):
        os.remove("data/user_account.session")

    context.bot_data["client"] = Client("data/user_account", api_id, api_hash)
    await context.bot_data["client"].connect()

    context.bot_data["msgId"] = await context.bot.sendMessage(
        update.effective_chat.id,
        "Send me your Phone number (+12345678900).\n\n Send /cancel to cancel sign in.",
    )

    return PHONE


async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["user_phone"] = update.message.text
    await context.bot.deleteMessage(update.effective_chat.id, update.message.id)

    context.bot_data["user_confirmation"] = await context.bot_data["client"].send_code(
        context.bot_data["user_phone"]
    )

    await context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=context.bot_data["msgId"]["message_id"],
        text="Now send me your confirmation code from Telegram app. (you can divide numbers by [space] for better results)\n\n Send /cancel to cancel sign in.",
    )

    return CONFIRMATION


async def login_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.bot_data["user_confirmation_code"] = update.message.text.strip(" ")
        await context.bot.deleteMessage(update.effective_chat.id, update.message.id)
        await context.bot_data["client"].sign_in(
            context.bot_data["user_phone"],
            context.bot_data["user_confirmation"].phone_code_hash,
            context.bot_data["user_confirmation_code"],
        )
        await context.bot_data["client"].disconnect()
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Login succeeded.",
        )
        login_purge(context)
        return ConversationHandler.END
    except SessionPasswordNeeded:
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Please enter your 2FA password.\n\n Send /cancel to cancel sign in.",
        )
        return PASSWORD
    except BadRequest:
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Code was Invalid, please start login from beginning.",
        )
        await context.bot_data["client"].disconnect()
        login_purge(context)
        return ConversationHandler.END


async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["user_password"] = update.message.text
    try:
        await context.bot.deleteMessage(update.effective_chat.id, update.message.id)
        await context.bot_data["client"].check_password(
            context.bot_data["user_password"]
        )
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Login succeeded",
        )
    except BadRequest:
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Password was Invalid, please start login from beginning.",
        )
    await context.bot_data["client"].disconnect()
    login_purge(context)
    return ConversationHandler.END


async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=context.bot_data["msgId"]["message_id"],
        text="login cancelled.",
    )
    await context.bot_data["client"].disconnect()
    login_purge(context)
    with contextlib.suppress(FileNotFoundError):
        os.remove("data/user_account.session")
    return ConversationHandler.END


login_handler = ConversationHandler(
    entry_points=[
        CommandHandler(
            "login", login_start, filters.Chat(username=os.getenv("username"))
        ),
    ],
    states={
        PHONE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                login_phone,
            ),
        ],
        CONFIRMATION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                login_code,
            ),
        ],
        PASSWORD: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                login_password,
            ),
        ],
    },
    fallbacks=[CommandHandler("cancel", login_cancel)],
)
