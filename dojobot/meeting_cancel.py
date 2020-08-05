from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler
import arrow

from db import DATABASE


def cancel_meeting_intent(message, intent):
    datetime = intent.params["datetime"]
    if datetime is not None:
        meeting = DATABASE.get_meeting_by_time(message.chat.id, datetime)
        if meeting is None:
            message.reply_text(
                "No meeting found with the given date and time. Please try again."
            )
        else:
            # cm: cancel_meeting
            keyboard = [
                [InlineKeyboardButton("Yes", callback_data=f"cm{meeting.meeting_id}")],
                [InlineKeyboardButton("No", callback_data="cancel_cancel_meeting")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message.reply_text(
                text=(
                    "Are you sure you want to cancel the meeting at "
                    f"<b>{meeting.formatted_datetime()}</b>"
                ),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )
    else:
        reply_markup = cancel_meeting_main_menu_keyboard(message.chat.id)
        if reply_markup is None:
            message.reply_text("No scheduled meetings.")
        else:
            message.reply_text(
                text="Choose the option in main menu:", reply_markup=reply_markup
            )


def cancel_meeting(update, context):
    query = update.callback_query
    meeting_id = query.data[2:]
    query.answer()
    meeting = DATABASE.get_meeting_by_id(meeting_id)

    if meeting:
        if meeting.datetime < arrow.now():
            temp_text = "Cannot cancel a meeting in the past!"
        else:
            temp_text = (
                f"You've canceled the meeting on <b>{meeting.formatted_datetime()}</b>"
            )
            DATABASE.cancel_remind(meeting_id, query.message.chat.id)
            DATABASE.delete(meeting)
    else:
        temp_text = "DATABASE ERROR! Can't delete this meeting"

    query.edit_message_text(text=temp_text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


# ---------------------------------------- MENU ----------------------------------------
def cancel_meeting_main_menu(update, context):
    query = update.callback_query
    query.answer()
    reply_markup = cancel_meeting_main_menu_keyboard(query.message.chat.id)

    if reply_markup is None:
        query.edit_message_text("No scheduled meetings")
    else:
        query.edit_message_text(text="Choose the meeting:", reply_markup=reply_markup)


def cancel_meeting_main_menu_keyboard(team_id):
    meetings = DATABASE.get_meetings(team_id, after=arrow.utcnow())
    keyboard = []
    reply_markup = None

    for meeting in meetings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    meeting.formatted_datetime(),
                    # cf: cancel_meeting_first
                    callback_data=f"cf{meeting.meeting_id}",
                )
            ]
        )

    if keyboard:
        keyboard.append(
            [InlineKeyboardButton("Cancel", callback_data="cancel_cancel_meeting")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


def cancel_meeting_first_menu(update, context):
    query = update.callback_query
    query.answer()
    temp = query.data[2:]
    query.edit_message_text(
        text=(
            "Are you sure you want to cancel the meeting at "
            f"<b>{DATABASE.get_meeting_by_id(temp).formatted_datetime()}</b>"
        ),
        reply_markup=cancel_meeting_first_menu_keyboard(temp),
        parse_mode=ParseMode.HTML,
    )


def cancel_meeting_first_menu_keyboard(temp):
    keyboard = [
        InlineKeyboardButton("Yes", callback_data=f"cm{temp}"),
        InlineKeyboardButton("No", callback_data="cancel_meeting_main"),
    ]

    return InlineKeyboardMarkup([keyboard])
