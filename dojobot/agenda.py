import arrow

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, Chat

import consts

from db import database
from dojobot import utils


def store_agenda_intent(context, message, intent):
    """Handle store agenda intent

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow
    """
    datetime = intent.params["datetime"]
    if datetime is not None:
        store_agenda_with_datetime(context, message, datetime)
    else:
        store_agenda_without_datetime(message)


def store_agenda_with_datetime(context, message, datetime):
    """Store agenda with a given meeting datetime

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
        if meeting.datetime < arrow.utcnow():
            message.reply_text(
                "Your meeting is in the past, you can only store agenda "
                "for meetings that haven't started."
            )
        else:
            # Check if agenda file exists, if so, ask if user wants to replace it
            if meeting.agenda:
                context.user_data[consts.CONFIRM_STORE_AGENDA] = True
                message.reply_text(
                    "A meeting agenda file already exists for this meeting, "
                    "do you want to replace it?",
                    reply_markup=store_agenda_confirm_keyboard(meeting.meeting_id),
                )
            else:
                context.user_data[consts.STORE_AGENDA] = meeting
                reply_markup = None

                if message.chat.type != Chat.PRIVATE:
                    reply_markup = ForceReply()

                message.reply_text(
                    "Please send me the meeting agenda file.", reply_markup=reply_markup
                )


def store_agenda_confirm_keyboard(meeting_id):
    """Get the confirm replace agenda keyboard

    Args:
        meeting_id (int): the meeting ID

    Returns:
        InlineKeyboardMarkup: the inline keyboard markup
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "Yes", callback_data=f"{consts.STORE_AGENDA},{meeting_id}",
            ),
            InlineKeyboardButton("No", callback_data=f"{consts.STORE_AGENDA},no",),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def store_agenda_without_datetime(message):
    """Store agenda without a given datetime, provide users with
        a list of meetings to choose from

    Args:
        message (Message): the Telegram message object
    """
    meetings = database.get_meetings(message.chat_id, after=arrow.utcnow())
    keyboard = []

    for meeting in meetings:
        keyboard.append(
            [
                InlineKeyboardButton(
                    meeting.formatted_datetime(),
                    callback_data=f"{consts.STORE_AGENDA},{meeting.meeting_id}",
                )
            ]
        )

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text(
            "Please select the meeting that you'll like to store the agenda.",
            reply_markup=reply_markup,
        )
    else:
        message.reply_text(
            "You haven't scheduled any meetings or your "
            "scheduled meetings have passed."
        )


def store_agenda_callback(update, context):
    """Store agenda callback query handler

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    _, meeting_id = query.data.split(",")

    if meeting_id == "no":
        query.edit_message_text("Cancelled for storing meeting agenda")
        if consts.CONFIRM_STORE_AGENDA in context.user_data:
            del context.user_data[consts.CONFIRM_STORE_AGENDA]
    else:
        edit_store_agenda_msg(context, query, meeting_id)


def edit_store_agenda_msg(context, query, meeting_id):
    """Edit the store agenda message

    Args:
        context (Context): the Telegram context object
        query (CallbackQuery): the Telegram callback query object
        meeting_id (int): the meeting ID
    """
    meeting = database.get_meeting_by_id(meeting_id)

    # Check if user has confirmed to replace existing agenda file
    if consts.CONFIRM_STORE_AGENDA in context.user_data:
        del context.user_data[consts.CONFIRM_STORE_AGENDA]
        if meeting is None:
            query.edit_message_text("The meeting is invalid. Please try again.")
        else:
            context.user_data[consts.STORE_AGENDA] = meeting
            text = "Please send me the meeting agenda file."
            utils.edit_query_message(context, query, text)

    # This callback query is to select a meeting, follow it up with either
    # replace existing agenda file or ask user to send through the file
    else:
        if meeting.agenda:
            context.user_data[consts.CONFIRM_STORE_AGENDA] = True
            query.edit_message_text(
                "A meeting agenda file already exists for this meeting, "
                "do you want to replace it?",
                reply_markup=store_agenda_confirm_keyboard(meeting_id),
            )
        else:
            context.user_data[consts.STORE_AGENDA] = meeting
            text = "Please send me the meeting agenda file."
            utils.edit_query_message(context, query, text)


def get_agenda_intent(update, context, intent):
    """Handle the get agenda intent

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
        intent (IntentResult): the intent result from Dialogflow
    """
    message = update.effective_message
    datetime = intent.params["datetime"]

    if datetime is not None:
        get_agenda_with_datetime(message, datetime)
    else:
        get_agenda_without_datetime(message)


def get_agenda_with_datetime(message, datetime):
    """Get agenda with a given meeting datetime

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
        if meeting.agenda:
            message.reply_document(
                meeting.agenda, caption="Here's your meeting agenda."
            )
        else:
            message.reply_text("No meeting agenda found for the meeting.")


def get_agenda_without_datetime(message):
    """Get agenda without a given datetime, provide user
        with a list of meetings to choose from

    Args:
        message (Message): the Telegram message object
    """
    meetings = database.get_meetings(message.chat_id)
    keyboard = []

    for meeting in meetings:
        if meeting.agenda:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        meeting.formatted_datetime(),
                        callback_data=f"{consts.GET_AGENDA},{meeting.meeting_id}",
                    )
                ]
            )

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text(
            "Please select the meeting that you'll like to retrieve the agenda.",
            reply_markup=reply_markup,
        )
    else:
        message.reply_text("No meeting agenda found.")


def get_agenda_callback(update, context):
    """Send through the meeting agenda if available

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    _, meeting_id = query.data.split(",")
    meeting = database.get_meeting_by_id(meeting_id)

    if meeting is None:
        query.edit_message_text("The meeting is invalid. Please try again.")
    elif not meeting.agenda:
        query.edit_message_text("There's no meeting agenda found for this meeting.")
    else:
        query.edit_message_text("Please see below for your meeting agenda.")
        context.bot.send_document(query.message.chat.id, meeting.agenda)
