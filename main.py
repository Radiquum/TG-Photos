import contextlib
import datetime
import logging
import os

from dotenv import load_dotenv
from PIL import ExifTags
from PIL import Image
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


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

from modules.database import (
    fetch_messages,
    search_in_DB,
    remove_from_DB,
    add_to_DB,
    edit_DB,
)

from modules.bot_login import login_handler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def db_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.isfile("data/user_account.session"):
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


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 0

    try:
        context.user_data["searchType"] = context.args[0].casefold()
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
                InlineKeyboardButton(
                    "✏️",
                    callback_data=f"edit {context.user_data['searchResults'][0][0]}",
                ),
                InlineKeyboardButton(
                    "❌",
                    callback_data=f"remove {context.user_data['searchResults'][0][0]}",
                ),
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
                InlineKeyboardButton(
                    "✏️",
                    callback_data=f"edit {context.user_data['searchResults'][0][0]}",
                ),
                InlineKeyboardButton(
                    "❌",
                    callback_data=f"remove {context.user_data['searchResults'][0][0]}",
                ),
            ],
        ]
    context.bot_data["reply_markup"] = reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data["searchResults"] == []:
        await context.bot.sendMessage(
            chat_id=update.effective_chat.id,
            text="Nothing found for this date. Retry your search.",
        )
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
                InlineKeyboardButton(
                    "✏️",
                    callback_data=f"edit {context.user_data['searchResults'][0 + n][0]}",
                ),
                InlineKeyboardButton(
                    "❌",
                    callback_data=f"remove {context.user_data['searchResults'][0 + n][0]}",
                ),
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
                InlineKeyboardButton(
                    "✏️",
                    callback_data=f"edit {context.user_data['searchResults'][0 + n][0]}",
                ),
                InlineKeyboardButton(
                    "❌",
                    callback_data=f"remove {context.user_data['searchResults'][0 + n][0]}",
                ),
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
                InlineKeyboardButton(
                    "✏️",
                    callback_data=f"edit {context.user_data['searchResults'][0 + n][0]}",
                ),
                InlineKeyboardButton(
                    "❌",
                    callback_data=f"remove {context.user_data['searchResults'][0 + n][0]}",
                ),
            ],
        ]
    context.bot_data["reply_markup"] = reply_markup = InlineKeyboardMarkup(keyboard)
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
    try:
        context.user_data["searchType"] = context.args[0].casefold()
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
    resp = query.data.strip("filename").strip()
    media_id = search_in_DB("filename", [0, resp])
    try:
        keyboard = [
            [
                InlineKeyboardButton("✏️", callback_data=f"edit {media_id[0][0]}"),
                InlineKeyboardButton("❌", callback_data=f"remove {media_id[0][0]}"),
            ],
        ]
        context.bot_data["reply_markup"] = reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.copyMessage(
            chat_id=update.effective_chat.id,
            from_chat_id=chatId,
            message_id=media_id[0][0],
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


TAG, MEDIA_BULK, ADD_TAG = range(3)


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["document_file"] = []
    await update.message.reply_text(
        "Send me a Photo or a Video as a Document. "
        "Send /finish to start uploading.\n\n"
        "Send /cancel to stop uploading.\n\n"
    )
    return MEDIA_BULK


async def media_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["document_file"].append(update.message.document)


async def getTime(update: Update, context: ContextTypes.DEFAULT_TYPE, document):
    createdTime = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")

    photo_file = await document.get_file()
    await photo_file.download_to_drive(document.file_name)
    img = Image.open(document.file_name)

    try:
        exif = {
            ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS
        }
        takenTime = datetime.datetime.strptime(
            exif["DateTime"], "%Y:%m:%d %H:%M:%S"
        ).strftime("%b %d, %Y, %I:%M:%S")
    except AttributeError:
        takenTime = createdTime

    img.close()
    os.remove(document.file_name)
    return takenTime, createdTime


async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Now, send me a tag(s)[devided by ","] you wish to add or send /skip if you don\'t want to.'
    )

    return ADD_TAG


async def add_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tags = update.message.text
    for item in context.bot_data["document_file"]:
        takenTime, createdTime = await getTime(Update, context, item)
        context.bot_data["docId"] = await context.bot.send_document(
            chat_id=os.getenv("chatId"),
            document=item,
            parse_mode="html",
            caption=f"""
<b>FileName</b>: {item.file_name}
<b>Taken</b>: {takenTime}
<b>Created</b>: {createdTime}
<b>Tags</b>: {tags}
""",
        )
        add_to_DB(
            context.bot_data["docId"].message_id,
            item.file_name,
            takenTime,
            createdTime,
            tags.casefold().strip().split(","),
        )

    await update.message.reply_text("Your media has been uploaded and tagged.")
    del context.bot_data["docId"]
    return ConversationHandler.END


async def skip_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    for item in context.bot_data["document_file"]:
        takenTime, createdTime = await getTime(Update, context, item)
        context.bot_data["docId"] = await context.bot.send_document(
            chat_id=os.getenv("chatId"),
            document=item,
            parse_mode="html",
            caption=f"""
<b>FileName</b>: {item.file_name}
<b>Taken</b>: {takenTime}
<b>Created</b>: {createdTime}
<b>Tags</b>:
    """,
        )
        add_to_DB(
            context.bot_data["docId"].message_id, item.file_name, takenTime, createdTime
        )
    await update.message.reply_text("Your media has been uploaded without tags.")
    return ConversationHandler.END


async def upload_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("upload cancelled.")

    return ConversationHandler.END


async def not_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("wrong attachment format.")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    global n
    global pages
    value = int(query.data.strip("remove"))

    try:
        remove_from_DB(value)
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
        await context.bot.deleteMessage(chat_id=os.getenv("chatId"), message_id=value)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Requested file(s) has been deleted.",
        )
    except (ValueError, IndexError, KeyError):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="File not found or already has been deleted.",
        )


NEW = range(1)


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    await context.bot.sendMessage(
        update.effective_chat.id,
        text='Enter new tags (divided by ","). Use -tag to remove a tag. send /cancel to cancel editing.',
    )
    context.chat_data["media_id"] = int(query.data.strip("edit"))
    return NEW


async def edit_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tag_list = update.message.text.split(",")
    post = edit_DB(context.chat_data["media_id"], tag_list)
    tags = [tag.tag for tag in post[3]]

    await context.bot.edit_message_caption(
        chat_id=os.getenv("chatId"),
        parse_mode="html",
        message_id=context.chat_data["media_id"],
        caption=f"""
<b>FileName</b>: {post[0]}
<b>Taken</b>: {post[1]}
<b>Created</b>: {post[2]}
<b>Tags</b>: {", ".join(tags)}
""",
    )
    await update.message.reply_text("tags has been updated.")

    context.bot_data["msgId"] = await context.bot.copyMessage(
        chat_id=update.effective_chat.id,
        from_chat_id=chatId,
        message_id=context.chat_data["media_id"],
        reply_markup=context.bot_data["reply_markup"],
    )
    del context.chat_data["media_id"]
    return ConversationHandler.END


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("edit cancelled.")
    context.bot_data["msgId"] = await context.bot.copyMessage(
        chat_id=update.effective_chat.id,
        from_chat_id=chatId,
        message_id=context.chat_data["media_id"],
        reply_markup=context.bot_data["reply_markup"],
    )
    del context.chat_data["media_id"]
    return ConversationHandler.END


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
    update_handler = CommandHandler(
        "update", db_update, filters.Chat(username=os.getenv("username"))
    )
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application = ApplicationBuilder().token(botToken).build()
    application.add_handler(start_handler)
    application.add_handler(searchList_handler)
    application.add_handler(search_handler)
    application.add_handler(update_handler)
    application.add_handler(CallbackQueryHandler(imgNavButtons, pattern="^img"))
    application.add_handler(CallbackQueryHandler(listNavButtons, pattern="^list"))
    application.add_handler(CallbackQueryHandler(getListMedia, pattern="^filename"))
    application.add_handler(CallbackQueryHandler(dummyButtons, pattern="^dummy$"))
    application.add_handler(CallbackQueryHandler(remove, pattern="^remove"))

    upload_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "upload", upload, filters.Chat(username=os.getenv("username"))
            ),
        ],
        states={
            MEDIA_BULK: [
                MessageHandler(
                    (filters.Document.VIDEO | filters.Document.IMAGE)
                    & ~filters.COMMAND,
                    media_bulk,
                ),
                MessageHandler(filters.ALL & ~filters.COMMAND, not_media),
                CommandHandler("finish", tag),
            ],
            ADD_TAG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_tag),
                CommandHandler("skip", skip_tag),
            ],
        },
        fallbacks=[CommandHandler("cancel", upload_cancel)],
    )
    application.add_handler(upload_handler)

    application.add_handler(login_handler)

    edit_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit, pattern="^edit"),
        ],
        states={
            NEW: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_tag,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel)],
    )
    application.add_handler(edit_handler)

    application.add_handler(unknown_handler)
    application.run_polling()
