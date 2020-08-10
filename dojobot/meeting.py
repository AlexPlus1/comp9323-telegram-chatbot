import arrow

from telegram import KeyboardButton, ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove

import consts
from db import DATABASE
from models import Meetings


def schedule_meeting_intent(context, message, intent):
    if intent.params["datetime"] < arrow.now():
        message.reply_text("Can't schedule a meeting in the past")
    else:
        if not check_meeting_conflict(message, intent):
            DATABASE.get_team(message.chat.id)
            new_meeting = Meetings(
                datetime=intent.params["datetime"].to("UTC"),
                duration=int(intent.params["duration"]),
                teams_id=message.chat.id,
            )
            DATABASE.insert(new_meeting)
            context.user_data[consts.SCHEDULE_MEETING] = new_meeting

            reply = "Your meeting has been scheduled on <b>{}</b> for <b>{} mins</b>.".format(
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
    meetings = DATABASE.get_meetings(message.chat_id)
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
                    "Can't schedule this meeting, time conflicting with meeting at <b>{}</b> lasting for <b>{} mins</b>.".format(
                        tmp_time, meeting.duration
                    ),
                    parse_mode=ParseMode.HTML,
                )
                break

    return is_conflict


def meeting_reminder_intent(context, message):
    if consts.SCHEDULE_MEETING in context.user_data:
        meeting = context.user_data[consts.SCHEDULE_MEETING]
        DATABASE.set_remind(meeting.meeting_id, message.chat.id)
        del context.user_data[consts.SCHEDULE_MEETING]

        message.reply_text(
            "A reminder has been set.", reply_markup=ReplyKeyboardRemove()
        )


def meeting_no_reminder_intent(context, message):
    if consts.SCHEDULE_MEETING in context.user_data:
        del context.user_data[consts.SCHEDULE_MEETING]
        message.reply_text(
            "Let me know if you'll like to set a reminder later.",
            reply_markup=ReplyKeyboardRemove(),
        )


def list_meetings_intent(message, intent):
    meetings = DATABASE.get_meetings(message.chat_id, after=arrow.utcnow())
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
