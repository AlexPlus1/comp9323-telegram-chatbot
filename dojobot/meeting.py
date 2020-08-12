import arrow

from telegram import KeyboardButton, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove

import consts
from db import database
from models import Meetings


def schedule_meeting_intent(context, message, intent):
    """Handle schedule meeting intent

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow
    """
    if intent.params["datetime"] < arrow.now():
        message.reply_text("Can't schedule a meeting in the past")
    else:
        if not check_meeting_conflict(message, intent):
            # Create the meeting in the database
            database.get_team(message.chat.id)
            new_meeting = Meetings(
                datetime=intent.params["datetime"].to("UTC"),
                duration=int(intent.params["duration"]),
                teams_id=message.chat.id,
            )
            database.insert(new_meeting)
            context.user_data[consts.SCHEDULE_MEETING] = new_meeting

            # Send message that meeting has been scheduled
            reply = "Your meeting has been scheduled on <b>{}</b> for <b>{} mins</b>.".format(
                new_meeting.formatted_datetime(), int(intent.params["duration"]),
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

            # Send message to ask if user wants to set meeting reminders
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
    """Check if meetings are conflicted

    Args:
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow

    Returns:
        bool: whether the meetings are conflicted
    """
    end = intent.params["datetime"].shift(minutes=int(intent.params["duration"]))
    meetings = database.get_meetings(message.chat_id)
    is_conflict = False

    for meeting in meetings:
        tmp_start = meeting.datetime
        tmp_end = tmp_start.shift(minutes=meeting.duration)
        if end <= tmp_start or intent.params["datetime"] >= tmp_end:
            continue
        else:
            is_conflict = True
            tmp_time = tmp_start.to(consts.TIMEZONE).format(consts.DATETIME_FORMAT)
            message.reply_text(
                "Can't schedule this meeting, time conflicting with meeting at <b>{}</b> lasting for <b>{} mins</b>.".format(
                    tmp_time, meeting.duration
                ),
                parse_mode=ParseMode.HTML,
            )
            break

    return is_conflict


def meeting_reminder_intent(context, message):
    """Handle set meeting reminder intent

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
    """
    if consts.SCHEDULE_MEETING in context.user_data:
        meeting = context.user_data[consts.SCHEDULE_MEETING]
        database.set_remind(meeting.meeting_id, message.chat.id)
        del context.user_data[consts.SCHEDULE_MEETING]

        message.reply_text(
            "A reminder has been set.", reply_markup=ReplyKeyboardRemove()
        )


def meeting_no_reminder_intent(context, message):
    """Handle not setting meeting reminder intent

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
    """
    if consts.SCHEDULE_MEETING in context.user_data:
        del context.user_data[consts.SCHEDULE_MEETING]
        message.reply_text(
            "Let me know if you'll like to set a reminder later.",
            reply_markup=ReplyKeyboardRemove(),
        )


def list_meetings_intent(message, intent):
    """Handle list meetings intent

    Args:
        message (Message): the Telegram message intent
        intent (IntentResult): the intent result from Dialogflow
    """
    meetings = database.get_meetings(message.chat_id, after=arrow.utcnow())
    reply = intent.fulfill_text + "\n"
    i = 1

    for meeting in meetings:
        tmp = "\n{}: {} for {} mins".format(
            i, meeting.formatted_datetime(), meeting.duration
        )
        reply += tmp
        i += 1

    if meetings:
        message.reply_text(reply)
    else:
        message.reply_text("There's no upcoming meetings")
