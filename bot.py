import argparse
import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

from models import *

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE = Database()


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)


def init_db():
    DATABASE.create_table()
    print("Database has been initialised")


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, greet_group))

    # Start the Bot
    updater.start_polling()
    LOGGER.info("Bot started polling")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def start(update, context):
    update.message.reply_text(
        "Hi! My name is Chatbot. Add me into a group chat to get started"
    )


def greet_group(update, context):
    message = update.effective_message
    for user in message.new_chat_members:
        if user.id == context.bot.id:
            chat_id = message.chat.id
            team = DATABASE.get_team(chat_id)

            if team is None:
                team = Teams(team_id=chat_id)
                DATABASE.insert(team)

            context.bot.send_message(
                chat_id,
                "Hello everyone! I'm your project helper and I've initialised a team for this group chat.",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--init_db", action="store_true", help="Initialise database"
    )
    args = parser.parse_args()

    if args.init_db:
        init_db()
    else:
        main()
