import contextlib
import datetime
import logging
import os
import time

from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

load_dotenv()

current_time = datetime.datetime.now()
botToken = os.getenv("botToken")
chatId = os.getenv("chatId")
api_id = os.getenv("appId")
api_hash = os.getenv("appHash")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from modules.database import fetch_messages, search_in_DB, remove_from_DB, add_to_DB


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def db_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.isfile("my_account.session"):
        await context.bot.sendMessage(
            update.effective_chat.id, "Updating posts DataBase... please wait..."
        )
        await fetch_messages()
        await context.bot.sendMessage(
            update.effective_chat.id, "DataBase has been updated."
        )
    else:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id, text="please /login first"
        )


PHONE, CONFIRMATION, PASSWORD = range(3)


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with contextlib.suppress(FileNotFoundError):
        os.remove("my_account.session")

    context.bot_data["msgId"] = await context.bot.sendMessage(
        update.effective_chat.id,
        "Send me your Phone number (+12345678900).\n\n Send /cancel to cancel sign in.",
    )
    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["user_phone"] = update.message.text
    await context.bot.deleteMessage(update.effective_chat.id, update.message.id)

    context.bot_data["client"] = Client("my_account", api_id, api_hash)
    await context.bot_data["client"].connect()

    await context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=context.bot_data["msgId"]["message_id"],
        text="Now send me your confirmation code from Telegram app.\n\n Send /cancel to cancel sign in.",
    )

    context.bot_data["user_confirmation"] = await context.bot_data["client"].send_code(
        context.bot_data["user_phone"]
    )

    return CONFIRMATION


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.bot_data["user_confirmation_code"] = update.message.text.strip(" ")
        await context.bot.deleteMessage(update.effective_chat.id, update.message.id)
        await context.bot_data["client"].sign_in(
            context.bot_data["user_phone"],
            context.bot_data["user_confirmation"].phone_code_hash,
            context.bot_data["user_confirmation_code"],
        )
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Login succeeded.",
        )
        # await context.bot_data["client"].disconnect()
        with contextlib.suppress(KeyError):
            del context.bot_data["user_phone"]
            del context.bot_data["user_confirmation"]
            del context.bot_data["user_confirmation_code"]
            del context.bot_data["user_password"]
        return ConversationHandler.END
    except SessionPasswordNeeded:
        await context.bot.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
            text="Please enter your 2FA password.\n\n Send /cancel to cancel sign in.",
        )
        return PASSWORD


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["user_password"] = update.message.text
    await context.bot.deleteMessage(update.effective_chat.id, update.message.id)
    await context.bot_data["client"].check_password(context.bot_data["user_password"])
    await context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=context.bot_data["msgId"]["message_id"],
        text="Login succeeded",
    )
    # await context.bot_data["client"].disconnect()
    with contextlib.suppress(KeyError):
        del context.bot_data["user_phone"]
        del context.bot_data["user_confirmation"]
        del context.bot_data["user_confirmation_code"]
        del context.bot_data["user_password"]
    return ConversationHandler.END


async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=context.bot_data["msgId"]["message_id"],
        text="login cancelled.",
    )
    with contextlib.suppress(KeyError):
        del context.bot_data["user_phone"]
        del context.bot_data["user_confirmation"]
        del context.bot_data["user_confirmation_code"]
        del context.bot_data["user_password"]
        # await context.bot_data["client"].disconnect()
    with contextlib.suppress(FileNotFoundError):
        os.remove("my_account.session")
    return ConversationHandler.END


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 0
    with contextlib.suppress(KeyError):
        await context.bot.deleteMessage(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
        )
    try:
        context.user_data["searchType"] = context.args[0]
        context.user_data["searchTerm"] = context.args
    except IndexError:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id, text="wrong or not complete command!"
        )
        return False
    await context.bot.deleteMessage(
        chat_id=update.effective_chat.id, message_id=update.effective_message.id
    )

    context.user_data["searchResults"] = search_in_DB(
        context.user_data.get("searchType"), context.user_data.get("searchTerm")
    )

    if len(context.user_data["searchResults"]) == 1:
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{n + 1}/{len(context.user_data['searchResults'])}",
                    callback_data="dummy",
                ),
                InlineKeyboardButton("❌", callback_data="remove"),
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("➡️", callback_data="img +1"),
            ],
            [
                InlineKeyboardButton(
                    f"{n + 1}/{len(context.user_data['searchResults'])}",
                    callback_data="dummy",
                ),
                InlineKeyboardButton("❌", callback_data="remove"),
            ],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data["searchResults"] == []:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id,
            text="Nothing found for this date. Retry your search.",
        )
        with contextlib.suppress(KeyError):
            del context.bot_data["msgId"]
        return False
    context.bot_data["msgId"] = await context.bot.copyMessage(
        chat_id=update.effective_chat.id,
        from_chat_id=chatId,
        message_id=context.user_data["searchResults"][0][0],
        reply_markup=reply_markup,
    )


async def imgNavButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    global n
    resp = query.data.strip("img")
    n += int(resp)

    if n != len(context.user_data["searchResults"]):
        keyboard = [
            [
                InlineKeyboardButton("⬅️", callback_data="img -1"),
                InlineKeyboardButton("➡️", callback_data="img +1"),
            ],
            [
                InlineKeyboardButton(
                    f"{n + 1}/{len(context.user_data['searchResults'])}",
                    callback_data="dummy",
                ),
                InlineKeyboardButton("❌", callback_data="remove"),
            ],
        ]

    if n == 0:
        keyboard = [
            [
                InlineKeyboardButton("➡️", callback_data="img +1"),
            ],
            [
                InlineKeyboardButton(
                    f"{n + 1}/{len(context.user_data['searchResults'])}",
                    callback_data="dummy",
                ),
                InlineKeyboardButton("❌", callback_data="remove"),
            ],
        ]

    if n == len(context.user_data["searchResults"]) - 1:
        keyboard = [
            [
                InlineKeyboardButton("⬅️", callback_data="img -1"),
            ],
            [
                InlineKeyboardButton(
                    f"{n + 1}/{len(context.user_data['searchResults'])}",
                    callback_data="dummy",
                ),
                InlineKeyboardButton("❌", callback_data="remove"),
            ],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot_data["msgId"] = await context.bot.copyMessage(
        chat_id=update.effective_chat.id,
        from_chat_id=chatId,
        message_id=context.user_data["searchResults"][0 + n][0],
        reply_markup=reply_markup,
    )
    await query.delete_message()


async def searchList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 1
    global offset
    offset = 0
    global pages
    pages = 0
    with contextlib.suppress(KeyError):
        await context.bot.deleteMessage(
            chat_id=update.effective_chat.id,
            message_id=context.bot_data["msgId"]["message_id"],
        )

    try:
        context.user_data["searchType"] = context.args[0]
        context.user_data["searchTerm"] = context.args
    except IndexError:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id, text="wrong or not complete command!"
        )
        return False
    await context.bot.deleteMessage(
        chat_id=update.effective_chat.id, message_id=update.effective_message.id
    )

    context.user_data["searchResults"] = search_in_DB(
        context.user_data.get("searchType"),
        context.user_data.get("searchTerm"),
        offset,
        limit=6,
    )
    if context.user_data["searchResults"] == []:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id,
            text="Nothing found for this date. Retry your search.",
        )
        with contextlib.suppress(KeyError):
            del context.bot_data["msgId"]
        return False

    pages = sum(
        i % 6 == 0
        for i in range(
            len(
                search_in_DB(
                    context.user_data.get("searchType"),
                    context.user_data.get("searchTerm"),
                )
            )
        )
    )
    keyboard = [
        [InlineKeyboardButton(x[1], callback_data=f"filename {x[1]}")]
        for x in context.user_data["searchResults"]
    ]
    if len(context.user_data["searchResults"]) == 6 and n != pages:
        keyboard.append([InlineKeyboardButton("➡️", callback_data="list +1")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot_data["msgId"] = await context.bot.sendMessage(
        chat_id=update.effective_chat.id,
        text=f"Available Media. Page {n}/{pages}",
        reply_markup=reply_markup,
    )


async def listNavButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    global n
    global offset
    resp = query.data.strip("list")
    n += int(resp)
    if int(resp) == -1:
        offset -= 6
    else:
        offset += 6

    context.user_data["searchResults"] = search_in_DB(
        context.user_data.get("searchType"),
        context.user_data.get("searchTerm"),
        offset,
        limit=6,
    )
    if context.user_data["searchResults"] == []:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id,
            text="Nothing found for this date. Retry your search.",
        )
        with contextlib.suppress(KeyError):
            del context.bot_data["msgId"]
        return False

    keyboard = [
        [InlineKeyboardButton(x[1], callback_data=f"filename {x[1]}")]
        for x in context.user_data["searchResults"]
    ]
    if n not in [pages, 1]:
        keyboard.append(
            [
                InlineKeyboardButton("⬅️", callback_data="list -1"),
                InlineKeyboardButton("➡️", callback_data="list +1"),
            ]
        )
    if n == 1 and len(context.user_data["searchResults"]) == 6:
        keyboard.append([InlineKeyboardButton("➡️", callback_data="list +1")])
    if n >= pages:
        keyboard.append([InlineKeyboardButton("⬅️", callback_data="list -1")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot_data["msgId"] = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.bot_data["msgId"]["message_id"],
        text=f"Available Media. Page {n}/{pages}",
        reply_markup=reply_markup,
    )


async def getListMedia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    resp = query.data.strip("filename ")
    context.user_data["media"] = search_in_DB("filename", [0, resp])
    keyboard = [
        [InlineKeyboardButton("❌", callback_data="remove")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.copyMessage(
            chat_id=update.effective_chat.id,
            from_chat_id=chatId,
            message_id=context.user_data["media"][0][0],
            reply_markup=reply_markup,
        )
    except IndexError:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id,
            text="Requested media is not found or has been deleted.",
        )


async def dummyButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "dummy":
        return


MEDIA, TAG, MEDIA_BULK = range(3)


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["document_file"] = []
    await update.message.reply_text(
        "Send me a Photo or a Video as a Document. "
        "Send /cancel to stop uploading.\n\n"
    )

    try:
        if context.args[0] == "bulk":
            await update.message.reply_text(
                "You can start uploading media until you type /finish"
            )
            return MEDIA_BULK
    except IndexError:
        return MEDIA


async def media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.bot_data["document_file"].append(update.message.document)
    await update.message.reply_text(
        'Now, send me a tag(s)[devided by ","] you wish to add or send /skip if you don\'t want to.'
    )
    return TAG


async def media_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["document_file"].append(update.message.document)


def getTime(update: Update, context: ContextTypes.DEFAULT_TYPE, document):
    photoTime = document.file_name.split(".")[0].split("_")
    day = datetime.datetime.strptime(photoTime[1], "%Y%m%d").strftime("%b %d, %Y,")
    time = datetime.datetime.strptime(photoTime[2][:6], "%H%M%S").strftime(
        "%I:%M:%S %p"
    )
    takenTime = f"{day} {time}"
    createdTime = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
    return takenTime, createdTime


async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tags = update.message.text
    await update.message.reply_text("Your media has been uploaded and tagged.")

    takenTime, createdTime = getTime(
        Update, context, context.bot_data["document_file"][0]
    )
    context.bot_data["docId"] = await context.bot.send_document(
        chat_id=os.getenv("chatId"),
        document=context.bot_data["document_file"][0],
        parse_mode="html",
        caption=f"""
<b>FileName</b>: {context.bot_data['document_file'][0].file_name}
<b>Taken</b>: {takenTime}
<b>Created</b>: {createdTime}
<b>Tags</b>: {tags}
""",
    )
    add_to_DB(
        context.bot_data["docId"].message_id,
        context.bot_data["document_file"][0].file_name,
        takenTime,
        tags.casefold().strip().split(","),
    )

    return ConversationHandler.END


async def skip_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    for x in context.bot_data["document_file"]:
        takenTime, createdTime = getTime(Update, context, x)
        context.bot_data["docId"] = await context.bot.send_document(
            chat_id=os.getenv("chatId"),
            document=x,
            parse_mode="html",
            caption=f"""
<b>FileName</b>: {x.file_name}
<b>Taken</b>: {takenTime}
<b>Created</b>: {createdTime}
<b>Tags</b>:
    """,
        )
        add_to_DB(context.bot_data["docId"].message_id, x.file_name, takenTime)
    await update.message.reply_text("Your media has been uploaded without tags.")
    return ConversationHandler.END


async def upload_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text("upload cancelled.")

    return ConversationHandler.END


async def not_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("wrong attachment format.")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        await query.answer()
        try:
            await query.delete_message()
            global n
            search_type, value = "id", context.user_data["searchResults"][0 + n][0]
            with contextlib.suppress(KeyError):
                del context.bot_data["msgId"]
        except (NameError, IndexError):
            search_type, value = "id", context.user_data["media"][0][0]
            global pages
    except NameError:
        search_type, value = context.args[0], context.args[1]

    if search_type in ["id", "filename"]:
        try:
            ID = remove_from_DB(search_type, value)
            with contextlib.suppress(NameError):
                pages = sum(
                    i % 6 == 0
                    for i in range(
                        len(
                            search_in_DB(
                                context.user_data.get("searchType"),
                                context.user_data.get("searchTerm"),
                            )
                        )
                    )
                )
            await context.bot.deleteMessage(
                chat_id=os.getenv("chatId"), message_id=ID.id
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Requested file(s) has been deleted.",
            )
        except (ValueError, IndexError, KeyError):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="File not found or already has been deleted.",
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="wrong or incomplete search type. (only id and filename are allowed)",
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Unknown command or Not authorized user."
    )


if __name__ == "__main__":
    start_handler = CommandHandler(
        "start", start, filters.Chat(username=os.getenv("username"))
    )
    searchList_handler = CommandHandler(
        "searchList", searchList, filters.Chat(username=os.getenv("username"))
    )
    search_handler = CommandHandler(
        "search", search, filters.Chat(username=os.getenv("username"))
    )
    remove_handler = CommandHandler(
        "remove", remove, filters.Chat(username=os.getenv("username"))
    )
    update_handler = CommandHandler(
        "update", db_update, filters.Chat(username=os.getenv("username"))
    )
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application = ApplicationBuilder().token(botToken).build()
    application.add_handler(start_handler)
    application.add_handler(searchList_handler)
    application.add_handler(search_handler)
    application.add_handler(remove_handler)
    application.add_handler(update_handler)
    application.add_handler(CallbackQueryHandler(imgNavButtons, pattern="^img"))
    application.add_handler(CallbackQueryHandler(listNavButtons, pattern="^list"))
    application.add_handler(CallbackQueryHandler(getListMedia, pattern="^filename"))
    application.add_handler(CallbackQueryHandler(dummyButtons, pattern="^dummy$"))
    application.add_handler(CallbackQueryHandler(remove, pattern="^remove$"))

    upload_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "upload", upload, filters.Chat(username=os.getenv("username"))
            ),
        ],
        states={
            MEDIA: [
                MessageHandler(
                    (filters.Document.VIDEO | filters.Document.IMAGE)
                    & ~filters.COMMAND,
                    media,
                ),
                MessageHandler(filters.ALL & ~filters.COMMAND, not_media),
            ],
            TAG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tag),
                CommandHandler("skip", skip_tag),
            ],
            MEDIA_BULK: [
                MessageHandler(
                    (filters.Document.VIDEO | filters.Document.IMAGE)
                    & ~filters.COMMAND,
                    media_bulk,
                ),
                MessageHandler(filters.ALL & ~filters.COMMAND, not_media),
                CommandHandler("finish", skip_tag),
            ],
        },
        fallbacks=[CommandHandler("cancel", upload_cancel)],
    )
    application.add_handler(upload_handler)

    login_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "login", login, filters.Chat(username=os.getenv("username"))
            ),
        ],
        states={
            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    phone,
                ),
            ],
            CONFIRMATION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    confirmation,
                ),
            ],
            PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    password,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", login_cancel)],
    )
    application.add_handler(login_handler)

    application.add_handler(unknown_handler)
    application.run_polling()
