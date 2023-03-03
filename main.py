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

from searchdb import searchDB

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def searchDate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    timestamp = time.mktime(time.strptime(" ".join(context.args), '%b %d %Y'))
    result = searchDB('timestamp', timestamp)
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

n = 0

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global n
    n = 0
    
    global TERM
    TERM = context.args[1].capitalize()
    global TYPE
    TYPE = context.args[0]
    result = searchDB(TYPE, TERM)
    keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="+1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if result == []:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="Nothing found for this date. Retry your search.")
        return(False)
    await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=result[0], reply_markup=reply_markup)
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

async def navButtons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'dummy':
        return
    global n
    n += int(query.data)
    await query.delete_message()
    
    result = searchDB(TYPE, TERM)
    # keyboard = [
    #     [
    #         InlineKeyboardButton("Prev", callback_data="-1"),
    #         InlineKeyboardButton("Next", callback_data="+1"),
    #     ],
    #     [InlineKeyboardButton(f"{n}/{len(result)}", callback_data="dummy")],
    # ]
    if n != len(result):
        keyboard = [
        [
            InlineKeyboardButton("Prev", callback_data="-1"),
            InlineKeyboardButton("Next", callback_data="+1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]

    if n == 0:
        keyboard = [
        [
            InlineKeyboardButton("Next", callback_data="+1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]
        
    if n == len(result) - 1:
        keyboard = [
        [
            InlineKeyboardButton("Prev", callback_data="-1"),
        ],
        [InlineKeyboardButton(f"{n + 1}/{len(result)}", callback_data="dummy")],
    ]
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.copyMessage(chat_id=update.effective_chat.id, from_chat_id=chatId, message_id=result[0 + n], reply_markup=reply_markup)

if __name__ == '__main__':
    
    start_handler = CommandHandler('start', start)
    searchDate_handler = CommandHandler('searchDate', searchDate)
    search_handler = CommandHandler('search', search)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    
    application = ApplicationBuilder().token(botToken).build()
    application.add_handler(start_handler)
    application.add_handler(search_handler)
    application.add_handler(searchDate_handler)
    application.add_handler(echo_handler)
    application.add_handler(CallbackQueryHandler(navButtons))
    
    application.run_polling()