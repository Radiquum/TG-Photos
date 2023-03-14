import os
import logging
import datetime
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CallbackQueryHandler
from modules.bot_login import login_handler
from modules.bot_upload import upload_handler
from modules.bot_post_actions import remove, edit_handler
from modules.bot_get_media import get_list_media, search_image_navigation, search_list_navigation
from modules.bot_misc import (start_handler, search_handler, searchList_handler, tagList_handler, update_handler,
                              unknown_handler, callback_commands_handler, log_handler)


load_dotenv()
botToken = os.getenv("botToken")
chatId = os.getenv("chatId")
current_time = datetime.datetime.now().strftime("%b%d%Y-%I%M%S%p")

logging.basicConfig(filename=f'logs/log-{current_time}.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filemode='w', level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    application = ApplicationBuilder().token(botToken).build()

    application.add_handler(start_handler)
    application.add_handler(search_handler)
    application.add_handler(searchList_handler)
    application.add_handler(tagList_handler)
    application.add_handler(update_handler)
    application.add_handler(log_handler)

    application.add_handler(CallbackQueryHandler(search_image_navigation, pattern="^img"))
    application.add_handler(CallbackQueryHandler(search_list_navigation, pattern="^list"))
    application.add_handler(CallbackQueryHandler(get_list_media, pattern="^filename"))
    application.add_handler(CallbackQueryHandler(remove, pattern="^remove"))

    application.add_handler(CallbackQueryHandler(callback_commands_handler, pattern="^/"))
    application.add_handler(CallbackQueryHandler(callback_commands_handler, pattern="^dummy$"))

    application.add_handler(upload_handler)
    application.add_handler(login_handler)
    application.add_handler(edit_handler)

    application.add_handler(unknown_handler)
    application.run_polling()
