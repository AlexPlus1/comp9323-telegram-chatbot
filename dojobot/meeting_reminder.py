import arrow
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

import consts
from db import database


def change_reminder_intent(message, intent):
    """Handle change meeting reminder intent

    Args:
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow
    """
    datetime = intent.params["datetime"]

    # Change meeting reminder with a given datetime
    if datetime is not None:
        meeting = database.get_meeting_by_time(message.chat.id, datetime)
        if meeting is None:
            message.reply_text(
                "No meeting found with the given date and time. Please try again."
            )
        else:
            if meeting.has_reminder:
                status = "on"
                button = "Turn off"
            else:
                status = "off"
                button = "Turn on"

            keyboard = [
                [
                    InlineKeyboardButton(
                        button,
                        callback_data=f"{consts.CHANGE_REMIND},{meeting.meeting_id}",
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message.reply_text(
                text=(
                    f"Reminder is currently <b>turned {status}</b> for "
                    f"the meeting on <b>{meeting.formatted_datetime()}</b>"
                ),
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )

    # Provide user with a list of meetings to choose from
    else:
        reply_markup = remind_main_menu_keyboard(message.chat.id)
        if reply_markup is None:
            message.reply_text("No meetings found or your meetings are in the past")
        else:
            message.reply_text(
                text="Select the meeting to change its reminder setting:",
                reply_markup=reply_markup,
            )


def change_remind(update, context):
    """Change meeting reminder callback query handler

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    _, meeting_id = query.data.split(",")
    chat_id = query.message.chat.id
    query.answer()
    meeting = database.get_meeting_by_id(meeting_id)

    if meeting is not None:
        if meeting.has_reminder:
            status = "off"
            database.cancel_remind(meeting_id, chat_id)
        else:
            status = "on"
            database.set_remind(meeting_id, chat_id)

        text = (
            f"You've <b>turned {status}</b> the reminder for "
            f"the meeting on <b>{meeting.formatted_datetime()}</b>"
        )
    else:
        text = "Invalid meeting, please try again."

    query.edit_message_text(text=text, parse_mode=ParseMode.HTML)


def cancel_del(update, context):
    """Cancel change meeting reminder callback query handler

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="What else can I do for you?")


# ---------------------------------------- MENU ----------------------------------------
def remind_main_menu(update, context):
    """Send the list of meetings for user to choose to change the reminder setting

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    reply_markup = remind_main_menu_keyboard(query.message.chat.id)

    if reply_markup is None:
        query.edit_message_text("No meetings found or your meetings are in the past")
    else:
        query.edit_message_text(
            text="Select the meeting to change its reminder setting:",
            reply_markup=reply_markup,
        )


def remind_main_menu_keyboard(chat_id):
    """Get the meetings keyboard for user to choose to change the reminder

    Args:
        chat_id (int): the chat ID

    Returns:
        InlineKeyboardMarkup: the meetings keyboard
    """
    meetings = database.get_meetings(chat_id, after=arrow.utcnow())
    keyboard = []
    reply_markup = None

    for meeting in meetings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    meeting.formatted_datetime(),
                    callback_data=f"rf{meeting.meeting_id}",
                )
            ]
        )

    if keyboard:
        keyboard.append(
            [InlineKeyboardButton("Cancel", callback_data="cancel_change_reminder")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


def remind_first_menu(update, context):
    """Show the current status of the meeting reminder, and allow user to change it

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    meeting_id = query.data[2:]
    meeting = database.get_meeting_by_id(meeting_id)

    if meeting is not None:
        if meeting.has_reminder:
            status = "on"
        else:
            status = "off"

        query.edit_message_text(
            text=(
                f"Reminder is currently <b>turned {status}</b> for "
                f"the meeting on <b>{meeting.formatted_datetime()}</b>"
            ),
            reply_markup=remind_first_menu_keyboard(meeting_id, meeting.has_reminder),
            parse_mode=ParseMode.HTML,
        )
    else:
        query.edit_message_text("Invalid meeting, please try again.")


def remind_first_menu_keyboard(meeting_id, check):
    """Get the keyboard for changing meeting reminder

    Args:
        meeting_id (int): the meeting ID
        check (bool): whether the meeting reminder is on or off

    Returns:
        InlineKeyboardMarkup: the keyboard to toggle meeting reminder
    """
    keyboard = [InlineKeyboardButton("Go back", callback_data="remind_main")]
    callback_data = f"{consts.CHANGE_REMIND},{meeting_id}"

    if check:
        keyboard.append(InlineKeyboardButton("Turn off", callback_data=callback_data))
    else:
        keyboard.append(InlineKeyboardButton("Turn on", callback_data=callback_data))

    return InlineKeyboardMarkup([keyboard])
