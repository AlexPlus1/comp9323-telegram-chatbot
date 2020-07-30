import argparse
import logging
import os

from dotenv import load_dotenv
from telegram import (
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
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
from models import Meetings, Users
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
    dp.add_handler(CommandHandler("start", start_msg))
    dp.add_handler(CommandHandler("help", help_msg))

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


def start_msg(update, context):
    update.message.reply_text(
        f"Hi! I'm {consts.BOT_NAME}. I'm here to help you to organise your "
        "group project and providing guidance along the way.\n\n"
        f"Type /help to see how to use {consts.BOT_NAME}."
    )


def help_msg(update, context):
    keyboard = [
        [KeyboardButton("Schedule meeting"), KeyboardButton("List meetings")],
        [KeyboardButton("Store notes"), KeyboardButton("Retrieve notes")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    update.effective_message.reply_text(
        "Please check the reply keyboard for some of the things I can do.\n\n"
        "You can also add me into a group chat where I can help you "
        "to manage your group project.\n\n",
        reply_markup=reply_markup,
    )


def greet_group(update, context):
    message = update.effective_message
    team = DATABASE.get_team(message.chat.id)

    for user in message.new_chat_members:
        if user.id == context.bot.id:
            chat_members = message.chat.get_administrators()
            names = []

            for chat_member in chat_members:
                add_user_team(chat_member.user, team)
                names.append(chat_member.user.first_name)

            message.reply_text(
                f"Hello everyone! I'm {consts.BOT_NAME} and "
                "I've initialised a team for this group chat. "
                "Invite your team members into this chat and "
                "I'll add them onto the team.\n\n"
                f"<i>Note that I've already added the admins ({','.join(names)}) "
                "onto the team</i>",
                quote=False,
                parse_mode=ParseMode.HTML,
            )
            message.reply_text(
                "Type /help if you're not sure what I can do", quote=False,
            )
        else:
            add_user_team(user, team)
            message.reply_text(
                f"Welcome {user.first_name}, I've added you to the team "
                f"for {message.chat.title}"
            )


def add_user_team(user, team):
    db_user = DATABASE.get_user(user.id)
    if db_user is None:
        db_user = Users(user_id=user.id, name=user.first_name, username=user.username)
        DATABASE.insert(db_user)

    if not any(x.team_id == team.team_id for x in db_user.teams):
        db_user.teams.append(team)
        DATABASE.commit()


def handle_text_msg(update, context):
    message = update.effective_message
    message.chat.send_action(ChatAction.TYPING)
    intent = get_intent(message.from_user.id, message.text)

    # if mssage for meeting scheduled is given
    if intent.all_params_present & (intent.intent == consts.SCHEDULE_MEETING):
        schedule_meeting_intent(context, message, intent)
    elif intent.intent == consts.MEETING_REMINDER:
        meeting_reminder_intent(context, message)
    elif intent.intent == consts.MEETING_NO_REMIDNER:
        meeting_no_reminder_intent(context, message)
    elif intent.intent == consts.MEETING_LIST:
        list_meetings_intent(message, intent)
    elif intent.intent == consts.STORE_NOTES:
        store_notes_intent(context, message, intent)
    elif intent.intent == consts.GET_NOTES:
        get_notes_intent(update, context, intent)
    elif intent.intent == consts.CANCEL_REMINDER:
        update.message.reply_text(
            text="Choose the option in main menu:",
            reply_markup=remind_main_menu_keyboard(),
        )
    else:
        message.reply_text(intent.fulfill_text)


def schedule_meeting_intent(context, message, intent):
    if intent.params["datetime"] < arrow.now():
        message.reply_text("Can't schedule a meeting in the past")
    else:
        if not check_meeting_conflict(message, intent):
            new_meeting = Meetings(
                datetime=intent.params["datetime"].to("UTC"),
                duration=int(intent.params["duration"]),
                teams=DATABASE.get_team(message.chat.id),
            )
            DATABASE.insert(new_meeting)
            context.user_data[consts.SCHEDULE_MEETING] = new_meeting

            reply = "Your meeting has been scheduled on <b>{}</b> for <b>{} minutes</b>.".format(
                new_meeting.formatted_datetime(), int(intent.params["duration"]),
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

            keyboard = [[KeyboardButton("Yes"), KeyboardButton("No")]]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, resize_keyboard=True, one_time_keyboard=True
            )
            message.reply_text(
                "Do you want to set a reminder for this meeting?",
                quote=False,
                reply_markup=reply_markup,
            )


def check_meeting_conflict(message, intent):
    end = intent.params["datetime"].shift(minutes=int(intent.params["duration"]))
    meetings = DATABASE.get_all_meetings(message.chat_id)
    is_conflict = False

    if meetings:
        for meeting in meetings:
            tmp_start = meeting.datetime
            tmp_end = tmp_start.shift(minutes=meeting.duration)
            if end <= tmp_start or intent.params["datetime"] >= tmp_end:
                continue
            else:
                is_conflict = True
                tmp_time = tmp_start.to(consts.TIMEZONE).format(consts.DATETIME_FORMAT)
                message.reply_text(
                    "Can't schedule this meeting, time conflicting with meeting at <b>{}</b> lasting for <b>{} minutes</b>.".format(
                        tmp_time, meeting.duration
                    ),
                    parse_mode=ParseMode.HTML,
                )
                break

    return is_conflict


def meeting_reminder_intent(context, message):
    if consts.SCHEDULE_MEETING in context.user_data:
        meeting = context.user_data[consts.SCHEDULE_MEETING]
        meeting.has_reminder = True
        DATABASE.commit()
        del context.user_data[consts.SCHEDULE_MEETING]

        message.reply_text(
            "A reminder has been set.", reply_markup=ReplyKeyboardRemove()
        )
        message.reply_text(meeting.meeting_suggestion())


def meeting_no_reminder_intent(context, message):
    if consts.SCHEDULE_MEETING in context.user_data:
        meeting = context.user_data[consts.SCHEDULE_MEETING]
        del context.user_data[consts.SCHEDULE_MEETING]

        message.reply_text(
            "Let me know if you'll like to set a reminder later.",
            reply_markup=ReplyKeyboardRemove(),
        )
        message.reply_text(meeting.meeting_suggestion())


def list_meetings_intent(message, intent):
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
        temp_text = "You've turned off the reminder!"
        DATABASE.cancel_remind(temp)
    else:
        temp_text = "You've turned on the reminder!"
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
        [InlineKeyboardButton("Cancel", callback_data="cancel_change_reminder")]
    )
    return InlineKeyboardMarkup(keyboard)


def remind_first_menu(update, context):
    query = update.callback_query
    query.answer()
    temp = query.data[2:]
    check = DATABASE.reminder_state(temp)

    if check:
        status = "on"
    else:
        status = "off"
    query.edit_message_text(
        text=f"Reminder is currently <b>turned {status}</b>",
        reply_markup=remind_first_menu_keyboard(temp, check),
        parse_mode=ParseMode.HTML,
    )


def remind_first_menu_keyboard(temp, check):
    keyboard = [InlineKeyboardButton("Go back", callback_data="remind_main")]
    if check:
        keyboard.append(InlineKeyboardButton("Turn off", callback_data=f"cr{temp}"))
    else:
        keyboard.append(InlineKeyboardButton("Turn on", callback_data=f"cr{temp}"))

    return InlineKeyboardMarkup([keyboard])


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
