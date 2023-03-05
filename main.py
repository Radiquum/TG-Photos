import os
import datetime
from dotenv import load_dotenv
load_dotenv()
import datetime
current_time = datetime.datetime.now()
botToken = os.getenv('botToken')
chatId = os.getenv('chatId')

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from modules.database import searchDB, searchDBlist, add_to_DataBase, remove_from_DataBase

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def searchDate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #timestamp = dt
    ##timestamp = time.mktime(time.strptime(" ".join(context.args), '%b %d %Y'))
    #result = searchDB('timestamp', timestamp)
    #message = await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
    pass

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 0
    try:
        await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=context.bot_data['msgId']['message_id'])
    except KeyError:
        pass    
    try:
        context.user_data['searchType'] = context.args[0]
        context.user_data['searchTerm'] = context.args[1].capitalize()
    except IndexError:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="wrong or not complete command!")
        return(False)
    await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=update.effective_message.id)
    
    context.user_data['searchResults'] = searchDB(context.user_data.get('searchType'), context.user_data.get('searchTerm'))
    
    if len(context.user_data['searchResults']) == 1:
        keyboard = [
            [InlineKeyboardButton(f"{n + 1}/{len(context.user_data['searchResults'])}", callback_data="dummy"),
            InlineKeyboardButton("❌", callback_data=f"remove")],
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("Next", callback_data="img +1"),
            ],
            [InlineKeyboardButton(f"{n + 1}/{len(context.user_data['searchResults'])}", callback_data="dummy"),
            InlineKeyboardButton("❌", callback_data=f"remove")],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if context.user_data['searchResults'] == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    context.bot_data['msgId'] = await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=context.user_data['searchResults'][0], reply_markup=reply_markup)

async def imgNavButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    global n
    resp = query.data.strip("img")
    n += int(resp)
    
    if n != len(context.user_data['searchResults']):
        keyboard = [
        [
            InlineKeyboardButton("Prev", callback_data="img -1"),
            InlineKeyboardButton("Next", callback_data="img +1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(context.user_data['searchResults'])}", callback_data="dummy"),
         InlineKeyboardButton("❌", callback_data="remove")],
    ]

    if n == 0:
        keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="img +1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(context.user_data['searchResults'])}", callback_data="dummy"),
         InlineKeyboardButton("❌", callback_data="remove")],
    ]
        
    if n == len(context.user_data['searchResults']) - 1:
        keyboard = [
        [
            InlineKeyboardButton("Prev", callback_data="img -1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(context.user_data['searchResults'])}", callback_data="dummy"),
         InlineKeyboardButton("❌", callback_data="remove")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.bot_data['msgId'] = await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=context.user_data['searchResults'][0 + n], reply_markup=reply_markup)
    await query.delete_message()

async def searchList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 1
    global offset
    offset = 0
    global pages
    pages = 0
    try:
        await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=context.bot_data['msgId']['message_id'])
    except KeyError:
        pass    
    try:
        context.user_data['searchType'] = context.args[0]
        context.user_data['searchTerm'] = context.args[1].capitalize()
    except IndexError:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="wrong or not complete command!")
        return(False)
    await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=update.effective_message.id)
    
    context.user_data['searchResults'] = searchDBlist(context.user_data.get('searchType'), context.user_data.get('searchTerm'), offset)
    if context.user_data['searchResults'] == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    
    for i in range(len(searchDB(context.user_data.get('searchType'), context.user_data.get('searchTerm')))):
        if i % 6 == 0: 
            pages += 1
    
    keyboard = []
    for x in context.user_data['searchResults']:
        keyboard.append([InlineKeyboardButton(x[0], callback_data=f"filename {x[0]}")])
    if len(context.user_data['searchResults']) == 6 and n != pages:
        keyboard.append([InlineKeyboardButton("Next", callback_data="list +1")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot_data['msgId'] = await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"Available Media. Page {n}/{pages}", reply_markup=reply_markup)

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
    
    context.user_data['searchResults'] = searchDBlist(context.user_data.get('searchType'), context.user_data.get('searchTerm'), offset)
    if context.user_data['searchResults'] == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    
    if context.user_data['searchResults'] == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    keyboard = []
    for x in context.user_data['searchResults'] :
        keyboard.append([InlineKeyboardButton(x[0], callback_data=f"filename {x[0]}")])
    if n != pages and n != 0:
        keyboard.append([InlineKeyboardButton("Prev", callback_data="list -1"),
            InlineKeyboardButton("Next", callback_data="list +1")])
    if n == 0 and len(context.user_data['searchResults']) == 6:
        keyboard.append([InlineKeyboardButton("Next", callback_data="list +1")])
    if n >= pages and len(context.user_data['searchResults']) < 6:
        keyboard.append([InlineKeyboardButton("Prev", callback_data="list -1")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot_data['msgId'] = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.bot_data['msgId']['message_id'], text=f"Available Media. Page {n}/{pages}", reply_markup=reply_markup)

async def getListMedia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    resp = query.data.strip("filename ")
    context.user_data['searchResults'] = searchDBlist('fileName', resp)
    keyboard = [
        [InlineKeyboardButton("❌", callback_data="remove")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=context.user_data['searchResults'][0][1], reply_markup=reply_markup)
    except IndexError:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Requested media is not found or has been deleted.")
        
async def dummyButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'dummy':
        return
    
MEDIA, TAG, MEDIA_BULK = range(3)

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.bot_data['document_file'] = []
    await update.message.reply_text(
        "Send me a Photo or a Video as a Document. "
        "Send /cancel to stop uploading.\n\n"
        )
    
    try:
        if context.args[0] == 'bulk':
            await update.message.reply_text("You can start uploading media until you type /finish")
            return MEDIA_BULK
    except IndexError:
        return MEDIA

async def media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.bot_data['document_file'] = update.message.document
    await update.message.reply_text(
        "Now, send me a tag you wish to add, or send /skip if you don't want to."
    )
    return TAG

async def media_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # sourcery skip: merge-list-append
    user = update.message.from_user
    context.bot_data['document_file'].append(update.message.document)

def getTime(update: Update, context: ContextTypes.DEFAULT_TYPE, document):
    photoTime = document.file_name.split(".")[0].split("_")
    day = datetime.datetime.strptime(photoTime[1], "%Y%m%d").strftime("%b %d, %Y,")
    time = datetime.datetime.strptime(photoTime[2][:6], "%H%M%S").strftime("%I:%M:%S %p")
    takenTime = f"{day} {time}"
    createdTime = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
    return takenTime, createdTime

async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    tags = update.message.text
    await update.message.reply_text(
        "Your media has been uploaded and tagged."
    )
    
    takenTime, createdTime = getTime(Update, context)
    context.bot_data['docId'] = await context.bot.send_document(chat_id=os.getenv('chatId'), document=context.bot_data['document_file'], parse_mode="html", caption=f"""
<b>FileName</b>: {context.bot_data['document_file'].file_name}
<b>Taken</b>: {takenTime}
<b>Created</b>: {createdTime}
<b>Tags</b>: {tags}
""")
    add_to_DataBase(context.bot_data['docId'].message_id, context.bot_data['document_file'].file_name, takenTime, tags)
    
    return ConversationHandler.END

async def skip_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    for x in context.bot_data['document_file']:
        takenTime, createdTime = getTime(Update, context, x)
        context.bot_data['docId'] = await context.bot.send_document(chat_id=os.getenv('chatId'), document=x, parse_mode="html", caption=f"""
    <b>FileName</b>: {x.file_name}
    <b>Taken</b>: {takenTime}
    <b>Created</b>: {createdTime}
    """)
        add_to_DataBase(context.bot_data['docId'].message_id, x.file_name, takenTime)
    await update.message.reply_text(
        "Your media has been uploaded without tags."
    )
    return ConversationHandler.END

async def upload_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        "upload cancelled."
    )

    return ConversationHandler.END

async def not_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        "wrong attachment format."
    )

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try: 
        query = update.callback_query
        await query.answer()
        try:
            await query.delete_message()
            global n
            search_type, value = 'postId', context.user_data['searchResults'][0 + n]
            del context.bot_data['msgId']
        except (NameError, IndexError):
            search_type, value = 'postId', context.user_data['searchResults'][0][1]
    except NameError:
        search_type, value = context.args[0], context.args[1]

    if search_type == 'postId' or search_type == 'fileName':
        try:
            ID = remove_from_DataBase(search_type, value)
            for x in ID:
                await context.bot.deleteMessage(chat_id=os.getenv('chatId'), message_id=x[1])
            if ID == []:
                raise ValueError
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Requested file(s) has been deleted.")
        except(ValueError, IndexError):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="File not found or already has been deleted.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="wrong or incomplete search type. (only postId and fileName are allowed)")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):        
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Unknown command or Not authorized user.")
    
if __name__ == '__main__':
    
    start_handler = CommandHandler('start', start, filters.Chat(username="@radiquum"))
    searchDate_handler = CommandHandler('searchDate', searchDate, filters.Chat(username="@radiquum"))
    searchList_handler = CommandHandler('searchList', searchList, filters.Chat(username="@radiquum"))
    search_handler = CommandHandler('search', search, filters.Chat(username="@radiquum"))
    remove_handler = CommandHandler('remove', remove, filters.Chat(username="@radiquum"))
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    
    application = ApplicationBuilder().token(botToken).build()
    application.add_handler(start_handler)
    application.add_handler(searchDate_handler)
    application.add_handler(searchList_handler)
    application.add_handler(search_handler)
    application.add_handler(remove_handler)
    application.add_handler(CallbackQueryHandler(imgNavButtons, pattern="^img"))
    application.add_handler(CallbackQueryHandler(listNavButtons, pattern="^list"))
    application.add_handler(CallbackQueryHandler(getListMedia, pattern="^filename"))
    application.add_handler(CallbackQueryHandler(dummyButtons, pattern="^dummy$"))
    application.add_handler(CallbackQueryHandler(remove, pattern="^remove$"))
    
    upload_handler = ConversationHandler(
        entry_points=[CommandHandler("upload", upload, filters.Chat(username="@radiquum")),],
        states={
            MEDIA: [MessageHandler((filters.Document.VIDEO | filters.Document.IMAGE) & ~filters.COMMAND, media), MessageHandler(filters.ALL & ~filters.COMMAND, not_media)],
            TAG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tag),
                CommandHandler("skip", skip_tag),
            ],
            MEDIA_BULK: [MessageHandler((filters.Document.VIDEO | filters.Document.IMAGE) & ~filters.COMMAND, media_bulk),
                         MessageHandler(filters.ALL & ~filters.COMMAND, not_media),
                         CommandHandler("finish", skip_tag)],
        },
        fallbacks=[CommandHandler("cancel", upload_cancel)],
    )
    application.add_handler(upload_handler)

    application.add_handler(unknown_handler)
    application.run_polling()