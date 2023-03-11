import os

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes

from modules.database import search_in_DB

chatId = os.getenv("chatId")


async def search_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def search_image_navigation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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


async def search_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def search_list_navigation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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


async def get_list_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
