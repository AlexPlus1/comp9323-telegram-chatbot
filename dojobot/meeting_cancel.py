import arrow
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from db import database


def cancel_meeting_intent(message, intent):
    """Handle cancel meeting intent

    Args:
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow
    """
    datetime = intent.params["datetime"]

    # Cancel meeting with a given meeting datetime
    if datetime is not None:
        meeting = database.get_meeting_by_time(message.chat.id, datetime)
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

    # Provide user with a list of meetings to choose to cancel
    else:
        reply_markup = cancel_meeting_main_menu_keyboard(message.chat.id)
        if reply_markup is None:
            message.reply_text("No scheduled meetings.")
        else:
            message.reply_text(
                text="Choose the option in main menu:", reply_markup=reply_markup
            )


def cancel_meeting(update, context):
    """Cancel meeting callback query handler

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object

    """
    query = update.callback_query
    meeting_id = query.data[2:]
    query.answer()
    meeting = database.get_meeting_by_id(meeting_id)

    if meeting:
        if meeting.datetime < arrow.now():
            temp_text = "Cannot cancel a meeting in the past!"
        else:
            temp_text = (
                f"You've canceled the meeting on <b>{meeting.formatted_datetime()}</b>"
            )
            database.cancel_remind(meeting_id, query.message.chat.id)
            database.delete_meeting(meeting_id)
    else:
        temp_text = "Invalid meeting, please try again."

    query.edit_message_text(text=temp_text, parse_mode=ParseMode.HTML)


# ---------------------------------------- MENU ----------------------------------------
def cancel_meeting_main_menu(update, context):
    """Send the list of meetings for user to choose to cancel

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    reply_markup = cancel_meeting_main_menu_keyboard(query.message.chat.id)

    if reply_markup is None:
        query.edit_message_text("No scheduled meetings")
    else:
        query.edit_message_text(text="Choose the meeting:", reply_markup=reply_markup)


def cancel_meeting_main_menu_keyboard(team_id):
    """Get the keyboard of meetings to choose to cancel

    Args:
        team_id (int): the team ID

    Returns:
        InlineKeyboardMarkUp: the keyboard of meetings
    """
    meetings = database.get_meetings(team_id, after=arrow.utcnow())
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
    """Send the confirm to cancle meeting keyboard

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    temp = query.data[2:]
    query.edit_message_text(
        text=(
            "Are you sure you want to cancel the meeting at "
            f"<b>{database.get_meeting_by_id(temp).formatted_datetime()}</b>"
        ),
        reply_markup=cancel_meeting_first_menu_keyboard(temp),
        parse_mode=ParseMode.HTML,
    )


def cancel_meeting_first_menu_keyboard(meeting_id):
    """Get the confirm cancel meeting keyboard

    Args:
        meeting_id (int): the meeting ID

    Returns:
        InlineKeyboardMarkup: the cancel meeting keyboard
    """
    keyboard = [
        InlineKeyboardButton("Yes", callback_data=f"cm{meeting_id}"),
        InlineKeyboardButton("No", callback_data="cancel_meeting_main"),
    ]

    return InlineKeyboardMarkup([keyboard])
