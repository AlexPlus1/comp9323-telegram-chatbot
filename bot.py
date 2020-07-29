import argparse
import logging
import os

from dotenv import load_dotenv
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)
import arrow

import consts
from db import DATABASE
from api_service import get_intent
from models import Teams, Meetings
from dojobot.notes import (
    store_notes_doc,
    store_notes_intent,
    get_notes_intent,
    store_notes_callback,
    get_notes_callback,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


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

    job = updater.job_queue
    job.run_repeating(check_meeting_reminder, interval=300, first=0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, greet_group))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_msg))
    dp.add_handler(MessageHandler(Filters.document, store_notes_doc))

    # show schedule and change remind
    dp.add_handler(CallbackQueryHandler(remind_main_menu, pattern="remind_main"))
    # dp.add_handler(CallbackQueryHandler(remind_first_menu, pattern='remind_sub'))

    dp.add_handler(CallbackQueryHandler(remind_first_menu, pattern=r"rf.*"))
    dp.add_handler(CallbackQueryHandler(change_remind, pattern=r"cr.*"))
    # dp.add_handler(CallbackQueryHandler(cancel_redmind, pattern=r'cr.*'))
    # dp.add_handler(CallbackQueryHandler(set_redmind, pattern=r'sr.*'))
    dp.add_handler(CallbackQueryHandler(cancel_del, pattern="cancel_change_reminder"))
    dp.add_handler(
        CallbackQueryHandler(store_notes_callback, pattern=rf"{consts.STORE_NOTES}.*")
    )
    dp.add_handler(
        CallbackQueryHandler(get_notes_callback, pattern=rf"{consts.GET_NOTES}.*")
    )

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
        handle_schedule_meeting_intent(message, intent, team)
    elif intent.intent == consts.MEETING_LIST:
        handle_list_meetings_intent(message, intent)
    elif intent.intent == consts.STORE_NOTES:
        store_notes_intent(context, message, intent)
    elif intent.intent == consts.GET_NOTES and intent.all_params_present:
        get_notes_intent(update, context, intent)
    elif intent.intent == consts.CANCEL_REMINDER:
        update.message.reply_text(
            text="Choose the option in main menu:",
            reply_markup=remind_main_menu_keyboard(),
        )
    else:
        message.reply_text(intent.fulfill_text)


def handle_schedule_meeting_intent(message, intent, team):
    if intent.params["datetime"] < arrow.now():
        message.reply_text("Can't schedule a meeting in the past")
    else:
        end = intent.params["datetime"].shift(minutes=int(intent.params["duration"]))
        meetings = DATABASE.get_all_meetings(message.chat_id)
        sign = 0
        if meetings:
            for meeting in meetings:
                tmp_start = meeting.datetime
                tmp_end = tmp_start.shift(minutes=meeting.duration)
                if end <= tmp_start:
                    continue
                elif intent.params["datetime"] >= tmp_end:
                    continue
                else:
                    sign = 1
                    tmp_time = tmp_start.to(consts.TIMEZONE).format(
                        consts.DATETIME_FORMAT
                    )
                    message.reply_text(
                        "Can't schedule this meeting, time conflicting with meeting at <b>{}</b> lasting for <b>{} minutes</b>.".format(
                            tmp_time, meeting.duration
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                    break
        if sign == 0:
            new_meeting = Meetings(
                datetime=intent.params["datetime"].to("UTC"),
                duration=int(intent.params["duration"]),
                has_reminder=intent.params["reminder"] == "on",
                teams=team,
            )
            DATABASE.insert(new_meeting)

            reply = "Your meeting has been scheduled on <b>{}</b> for <b>{} minutes</b>.\n\nReminder: {}".format(
                new_meeting.formatted_datetime(),
                int(intent.params["duration"]),
                intent.params["reminder"],
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)


def handle_list_meetings_intent(message, intent):
    meetings = DATABASE.get_all_meetings(message.chat_id)
    reply = intent.fulfill_text + "\n"
    if meetings:
        i = 1
        for meeting in meetings:
            tmp = "\n{}: {} for {} minutes".format(
                i, meeting.formatted_datetime(), meeting.duration
            )
            reply += tmp
            i += 1
        message.reply_text(reply)
    else:
        message.reply_text("There's no upcoming meetings")


###############################  REMINDER ############################################
def check_meeting_reminder(context: CallbackContext):
    meetings = DATABASE.get_all_my_meetings()
    for m in meetings:
        if m.has_reminder:
            temp_time = arrow.get(m.datetime)
            cur_time = arrow.utcnow()
            range = temp_time - cur_time
            if 86400 <= range.seconds < 86700:
                context.bot.send_message(
                    chat_id=m.teams_id, text="Your meeting will start in 24 hours!"
                )
            elif 3600 <= range.seconds < 3900:
                # elif  300 <= range.seconds < 340:
                context.bot.send_message(
                    chat_id=m.teams_id, text="Your meeting will start in an hour!"
                )
            elif 300 <= range.seconds < 600:
                # elif 0 <= range.seconds < 299:
                context.bot.send_message(
                    chat_id=m.teams_id, text="Your meeting will start soon!"
                )


def change_remind(update, context):

    query = update.callback_query
    temp = query.data[2:]
    query.answer()
    check = DATABASE.reminder_state(temp)
    if check:
        temp_text = "You have cancelled the reminder!"
        DATABASE.cancel_remind(temp)
    else:
        temp_text = "You have set the reminder!"
        DATABASE.set_remind(temp)

    query.edit_message_text(text=temp_text)
    return ConversationHandler.END


def cancel_del(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="What else can I do for you?")
    return ConversationHandler.END


###############################  MENU ############################################
def remind_main_menu(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="Choose the meeting:", reply_markup=remind_main_menu_keyboard()
    )


def remind_main_menu_keyboard():
    meetings = DATABASE.get_all_my_meetings()
    keyboard = []
    for meeting in meetings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    meeting.formatted_datetime(),
                    callback_data=f"rf{meeting.meeting_id}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                "I dont want to change reminder", callback_data="cancel_change_reminder"
            )
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def remind_first_menu(update, context):
    query = update.callback_query
    query.answer()
    temp = query.data[2:]
    check = DATABASE.reminder_state(temp)
    if check == True:
        reminder = "reminider state: on"
    else:
        reminder = "reminider state: off"
    query.edit_message_text(
        text=reminder, reply_markup=remind_first_menu_keyboard(temp)
    )


def remind_first_menu_keyboard(temp):
    keyboard = [
        [InlineKeyboardButton("cancel reminder", callback_data=f"cr{temp}")],
        [InlineKeyboardButton("set reminder", callback_data=f"cr{temp}")],
        [InlineKeyboardButton("schedules", callback_data="remind_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


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
