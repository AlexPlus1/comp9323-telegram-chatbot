import argparse
import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)
import arrow

import consts
from api_service import get_intent
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
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_msg))
    # dp.add_handler(, group=1)

    # Start the Bot
    updater.start_polling()
    LOGGER.info("Bot started polling")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def start(update, context):
    update.message.reply_text(
        f"Hi! I'm {consts.BOT_NAME}. Add me into a group chat to get started"
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
                f"Hello everyone! I'm {consts.BOT_NAME} and I've initialised a team for this group chat.",
            )


def handle_text_msg(update, context):
    message = update.effective_message
    message.chat.send_action(ChatAction.TYPING)
    # init the team
    chat_id = message.chat.id
    team = DATABASE.get_team(chat_id)
    if team is None:
        team = Teams(team_id=chat_id)
        DATABASE.insert(team)
    
    intent = get_intent(message.from_user.id, message.text)
    
    # if mssage for meeting scheduled is given
    if intent.all_params_present & (intent.intent == consts.SCHEDULE_MEETING):
        if intent.params["datetime"] < arrow.now():
            message.reply_text("Can't schedule a meeting in the past")
        else:
            end = intent.params["datetime"].shift(minutes=int(intent.params["duration"]))
            # meetings = DATABASE.get_all_meetings()
            meetings = DATABASE.get_all_meetings(chat_id)
            sign = 0
            if meetings:
                for meeting in meetings:
                    tmp_start = arrow.get(meeting.date_time)
                    tmp_end = tmp_start.shift(minutes=meeting.duration)
                    if end <= tmp_start:
                        continue
                    elif intent.params["datetime"] >= tmp_end:
                        continue
                    else:
                        sign = 1
                        tmp_time = tmp_start.to('local').format('YYYY-MM-DD HH:mm ZZZ')
                        message.reply_text("Can't schedule this meeting, time conflicting with meeting at {} lasting for {} minutes".format(tmp_time, meeting.duration))
                        break
            if sign == 0:
                time = intent.params["datetime"].format('YYYY-MM-DD HH:mm ZZZ')
                reply = "Your meeting has been scheduled on {} for {} minutes.".format(time, int(intent.params["duration"]))
                new_meeting = Meetings(date_time=intent.params["datetime"].to("UTC").datetime, duration=int(intent.params["duration"]), has_reminder=True, notes='', teams=team)
                DATABASE.insert(new_meeting)
                message.reply_text(reply)
    elif intent.intent == consts.MEETING_LIST:
        meetings = DATABASE.get_all_meetings(chat_id)
        reply = intent.fulfill_text
        if meetings:
            i = 1
            for meeting in meetings:
                time = arrow.get(meeting.date_time).to('local').format('YYYY-MM-DD HH:mm ZZZ')
                tmp = "\n{}: {} for {} minutes".format(i, time, meeting.duration)
                reply += tmp
                i += 1
            message.reply_text(reply)
        else:
            message.reply_text("There's no upcoming meetings")
    else:
        message.reply_text(intent.fulfill_text)


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
