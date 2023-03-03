import os
import time
from dotenv import load_dotenv
load_dotenv()

botToken = os.getenv('botToken')
chatId = os.getenv('chatId')

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from searchdb import searchDB, searchDBlist, searchMedia

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def searchDate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    timestamp = time.mktime(time.strptime(" ".join(context.args), '%b %d %Y'))
    result = searchDB('timestamp', timestamp)
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 0
    
    try:
        global TERM
        TERM = context.args[1].capitalize()
        global TYPE
        TYPE = context.args[0]
    except IndexError:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="wrong or not complete command!")
        return(False)
    await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=update.effective_message.id)
    
    result = searchDB(TYPE, TERM)
    keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="img +1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if result == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=result[0], reply_markup=reply_markup)

async def imgNavButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    global n
    resp = query.data.strip("img")
    n += int(resp)
    await query.delete_message()
    result = searchDB(TYPE, TERM)
    if n != len(result):
        keyboard = [
        [
            InlineKeyboardButton("Prev", callback_data="img -1"),
            InlineKeyboardButton("Next", callback_data="img +1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]

    if n == 0:
        keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="img +1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]
        
    if n == len(result) - 1:
        keyboard = [
        [
            InlineKeyboardButton("Prev", callback_data="img -1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=result[0 + n], reply_markup=reply_markup)

async def searchList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 1
    global offset
    offset = 0
    global pages
    pages = 0
    try:
        global TERM
        TERM = context.args[1].capitalize()
        global TYPE
        TYPE = context.args[0]
    except IndexError:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="wrong or not complete command!")
        return(False)
    
    await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=update.effective_message.id)
    
    result = searchDBlist(TYPE, TERM, offset)
    if result == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    
    for i in range(len(searchDB(TYPE, TERM))):
        if i % 6 == 0: 
            pages += 1
    
    keyboard = []
    for x in result:
        keyboard.append([InlineKeyboardButton(x, callback_data=f"filename {x}")])
    if len(result) == 6 and n != pages:
        keyboard.append([InlineKeyboardButton("Next", callback_data="list +1")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"Available Media. Page {n}/{pages}", reply_markup=reply_markup)

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
    await query.delete_message()
    result = searchDBlist(TYPE, TERM, offset)
    
    if result == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    keyboard = []
    for x in result :
        keyboard.append([InlineKeyboardButton(x, callback_data=f"filename {x}")])
    if n != pages and n != 0:
        keyboard.append([InlineKeyboardButton("Prev", callback_data="list -1"),
            InlineKeyboardButton("Next", callback_data="list +1")])
    if n == 0 and len(result) == 6:
        keyboard.append([InlineKeyboardButton("Next", callback_data="list +1")])
    if n >= pages and len(result) < 6:
        keyboard.append([InlineKeyboardButton("Prev", callback_data="list -1")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"Available Media. Page {n}/{pages}", reply_markup=reply_markup)

async def getListMedia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    resp = query.data.strip("filename ")
    result = searchMedia('fileName', resp)
    await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=result[0])

async def dummyButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'dummy':
        return

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")
    
if __name__ == '__main__':
    
    start_handler = CommandHandler('start', start)
    searchDate_handler = CommandHandler('searchDate', searchDate)
    searchList_handler = CommandHandler('searchList', searchList)
    search_handler = CommandHandler('search', search)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    
    application = ApplicationBuilder().token(botToken).build()
    application.add_handler(start_handler)
    application.add_handler(search_handler)
    application.add_handler(searchDate_handler)
    application.add_handler(searchList_handler)
    application.add_handler(echo_handler)
    application.add_handler(CallbackQueryHandler(imgNavButtons, pattern="^img"))
    application.add_handler(CallbackQueryHandler(listNavButtons, pattern="^list"))
    application.add_handler(CallbackQueryHandler(getListMedia, pattern="^filename"))
    application.add_handler(CallbackQueryHandler(dummyButtons, pattern="^dummy$"))
    application.add_handler(unknown_handler)
    
    application.run_polling()