import arrow

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Chat, ForceReply

import consts

from db import database
from dojobot import utils


def store_notes_intent(context, message, intent):
    """Handle store notes intent

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow
    """
    datetime = intent.params["datetime"]
    if datetime is not None:
        store_notes_with_datetime(context, message, datetime)
    else:
        store_notes_without_datetime(message)


def store_notes_with_datetime(context, message, datetime):
    """Store notes with a given meeting datetime

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
        datetime (Arrow): the arrow datetime
    """
    meeting = database.get_meeting_by_time(message.chat_id, datetime)
    if meeting is None:
        message.reply_text(
            "No meeting found with the given date and time. Please try again."
        )
    else:
        if meeting.datetime > arrow.utcnow():
            message.reply_text(
                "Your meeting hasn't started yet, you can only store notes "
                "after you've finished your meeting."
            )
        else:
            # Check if meeting notes file exists, if so, ask if user wants to replace it
            if meeting.notes:
                context.user_data[consts.CONFIRM_STORE_NOTES] = True
                message.reply_text(
                    "A meeting notes file already exists for this meeting, "
                    "do you want to replace it?",
                    reply_markup=store_notes_confirm_keyboard(meeting.meeting_id),
                )
            else:
                context.user_data[consts.STORE_NOTES] = meeting
                reply_markup = None

                if message.chat.type != Chat.PRIVATE:
                    reply_markup = ForceReply()

                message.reply_text(
                    "Please send me the meeting notes file.", reply_markup=reply_markup
                )


def store_notes_confirm_keyboard(meeting_id):
    """Get the keyboard to confirm to replace meeting notes file

    Args:
        meeting_id (int): the meeting ID

    Returns:
        InlineKeyboardMarkup: the confirm keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "Yes", callback_data=f"{consts.STORE_NOTES},{meeting_id}",
            ),
            InlineKeyboardButton("No", callback_data=f"{consts.STORE_NOTES},no",),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def store_notes_without_datetime(message):
    """Store notes without a given datetime, provide user
        with a list of meetings to choose from

    Args:
        message (Message): the Telegram message object
    """
    meetings = database.get_meetings(message.chat_id, before=arrow.utcnow())
    keyboard = []

    for meeting in meetings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    meeting.formatted_datetime(),
                    callback_data=f"{consts.STORE_NOTES},{meeting.meeting_id}",
                )
            ]
        )

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text(
            "Please select the meeting that you'll like to store the notes.",
            reply_markup=reply_markup,
        )
    else:
        message.reply_text(
            "You haven't scheduled any meetings or your "
            "scheduled meetings haven't passed yet."
        )


def store_notes_callback(update, context):
    """Store meeting notes callback query handler

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    _, meeting_id = query.data.split(",")

    if meeting_id == "no":
        query.edit_message_text("Cancelled for storing meeting notes")
        if consts.CONFIRM_STORE_NOTES in context.user_data:
            del context.user_data[consts.CONFIRM_STORE_NOTES]
    else:
        edit_store_notes_msg(context, query, meeting_id)


def edit_store_notes_msg(context, query, meeting_id):
    """Edit store notes query message

    Args:
        context (Context): the Telegram context object
        query (CallbackQuery): the Telegram callback query object
        meeting_id (int): the meeting ID
    """
    meeting = database.get_meeting_by_id(meeting_id)

    # Check if user has confirmed to replace existing meeting notes file
    if consts.CONFIRM_STORE_NOTES in context.user_data:
        del context.user_data[consts.CONFIRM_STORE_NOTES]
        if meeting is None:
            query.edit_message_text("The meeting is invalid. Please try again.")
        else:
            context.user_data[consts.STORE_NOTES] = meeting
            text = "Please send me the meeting notes file."
            utils.edit_query_message(context, query, text)
    else:

        # User has picked a meeting and notes file exists,
        # ask if user wants to replace it
        if meeting.notes:
            context.user_data[consts.CONFIRM_STORE_NOTES] = True
            query.edit_message_text(
                "A meeting notes file already exists for this meeting, "
                "do you want to replace it?",
                reply_markup=store_notes_confirm_keyboard(meeting_id),
            )
        else:
            context.user_data[consts.STORE_NOTES] = meeting
            text = "Please send me the meeting notes file."
            utils.edit_query_message(context, query, text)


def get_notes_intent(update, context, intent):
    """Handle get notes intent

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
        intent (IntentResult): the intent result from Dialogflow
    """
    message = update.effective_message
    datetime = intent.params["datetime"]

    if datetime is not None:
        get_notes_with_datetime(message, datetime)
    else:
        get_notes_without_datetime(message)


def get_notes_with_datetime(message, datetime):
    """Get notes with a given meeting datetime

    Args:
        message (Message): the Telegram message object
        datetime (Arrow): the arrow datetime
    """
    meeting = database.get_meeting_by_time(message.chat_id, datetime)
    if meeting is None:
        message.reply_text(
            "No meeting found with the given date and time. Please try again."
        )
    else:
        if meeting.notes:
            message.reply_document(meeting.notes, caption="Here's your meeting notes.")
        else:
            message.reply_text("No meeting notes found for the meeting.")


def get_notes_without_datetime(message):
    """Get notes without a given datetime, provide user
        with a list of meetings to choose from

    Args:
        message (Message): the Telegram message object
    """
    meetings = database.get_meetings(message.chat_id)
    keyboard = []

    for meeting in meetings:
        if meeting.notes:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        meeting.formatted_datetime(),
                        callback_data=f"{consts.GET_NOTES},{meeting.meeting_id}",
                    )
                ]
            )

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text(
            "Please select the meeting that you'll like to retrieve the notes.",
            reply_markup=reply_markup,
        )
    else:
        message.reply_text("No meeting notes found.")


def get_notes_callback(update, context):
    """Get meeting notes if available

    Args:
        update (Update): the Update object
        context (Context): the Context object
    """
    query = update.callback_query
    query.answer()
    _, meeting_id = query.data.split(",")
    meeting = database.get_meeting_by_id(meeting_id)

    if meeting is None:
        query.edit_message_text("The meeting is invalid. Please try again.")
    elif not meeting.notes:
        query.edit_message_text("There's no meeting notes found for this meeting.")
    else:
        query.edit_message_text("Please see below for your meeting notes.")
        context.bot.send_document(query.message.chat.id, meeting.notes)
