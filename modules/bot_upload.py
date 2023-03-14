import datetime
import os

from PIL import ExifTags
from PIL import Image
from telegram import Update
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from modules.database import add_to_db

UPLOAD_MEDIA, ADD_TAG = range(2)


async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.bot_data["document_file"] = []
    await update.message.reply_text(
        "Send me a Photo or a Video as a Document. "
        "Send /finish to start uploading.\n\n"
        "Send /cancel to stop uploading.\n\n"
    )
    return UPLOAD_MEDIA


async def upload_receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["document_file"].append(update.message.document)


async def upload_get_media_time(document):
    createdtime = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")

    photo_file = await document.get_file()
    await photo_file.download_to_drive(document.file_name)
    img = Image.open(document.file_name)

    try:
        exif = {
            ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS
        }
        takentime = datetime.datetime.strptime(
            exif["DateTime"], "%Y:%m:%d %H:%M:%S"
        ).strftime("%b %d, %Y, %I:%M:%S %p")
    except AttributeError:
        takentime = createdtime

    img.close()
    os.remove(document.file_name)
    return takentime, createdtime


async def upload_tag(update: Update) -> int:
    await update.message.reply_text(
        'Now, send me a tag(s)[divided by ","] you wish to add or send /skip if you don\'t want to.'
    )

    return ADD_TAG


async def upload_add_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tags = update.message.text
    await update.message.reply_text("Media upload has been started, please wait...")
    for item in context.bot_data["document_file"]:
        takentime, createdtime = await upload_get_media_time(item)
        context.bot_data["docId"] = await context.bot.send_document(
            chat_id=os.getenv("chatId"),
            document=item,
            parse_mode="html",
            caption=f"""
<b>FileName</b>: {item.file_name}
<b>Taken</b>: {takentime}
<b>Created</b>: {createdtime}
<b>Tags</b>: {tags}
""",
        )
        add_to_db(
            context.bot_data["docId"].message_id,
            item.file_name,
            takentime,
            createdtime,
            tags.casefold().strip().split(","),
        )
    await update.message.reply_text("Your media has been uploaded and tagged.")
    return ConversationHandler.END


async def upload_skip_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Media upload has been started, please wait...")
    for item in context.bot_data["document_file"]:
        takentime, createdtime = await upload_get_media_time(item)
        context.bot_data["docId"] = await context.bot.send_document(
            chat_id=os.getenv("chatId"),
            document=item,
            parse_mode="html",
            caption=f"""
<b>FileName</b>: {item.file_name}
<b>Taken</b>: {takentime}
<b>Created</b>: {createdtime}
<b>Tags</b>:
    """,
        )
        add_to_db(
            context.bot_data["docId"].message_id,
            item.file_name,
            takentime,
            createdtime
        )
    await update.message.reply_text("Your media has been uploaded without tags.")
    return ConversationHandler.END


async def upload_cancel(update: Update) -> int:
    await update.message.reply_text("upload cancelled.")
    return ConversationHandler.END


async def upload_wrong_format(update: Update):
    await update.message.reply_text("wrong attachment format.")


upload_handler = ConversationHandler(
    entry_points=[
        CommandHandler(
            "upload", upload_start, filters.Chat(username=os.getenv("username"))
        ),
    ],
    states={
        UPLOAD_MEDIA: [
            MessageHandler(
                (filters.Document.VIDEO | filters.Document.IMAGE) & ~filters.COMMAND,
                upload_receive_media,
            ),
            MessageHandler(filters.ALL & ~filters.COMMAND, upload_wrong_format),
            CommandHandler("finish", upload_tag),
        ],
        ADD_TAG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, upload_add_tag),
            CommandHandler("skip", upload_skip_tag),
        ],
    },
    fallbacks=[CommandHandler("cancel", upload_cancel)],
)
