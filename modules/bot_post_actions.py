import contextlib
import os

from telegram import Update
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from modules.database import edit_DB
from modules.database import remove_from_DB
from modules.database import search_in_DB

chatId = os.getenv("chatId")


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
