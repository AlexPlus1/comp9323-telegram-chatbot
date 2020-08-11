import arrow

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import consts
from db import database


def store_notes_intent(context, message, intent):
    datetime = intent.params["datetime"]
    if datetime is not None:
        store_notes_with_datetime(context, message, datetime)
    else:
        store_notes_without_datetime(message)


def store_notes_with_datetime(context, message, datetime):
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
            if meeting.notes:
                context.user_data[consts.CONFIRM_STORE_NOTES] = True
                message.reply_text(
                    "A meeting notes file already exists for this meeting, "
                    "do you want to replace it?",
                    reply_markup=store_notes_confirm_keyboard(meeting.meeting_id),
                )
            else:
                context.user_data[consts.STORE_NOTES] = meeting
                message.reply_text("Please send me the meeting notes file.")


def store_notes_confirm_keyboard(meeting_id):
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
    meeting = database.get_meeting_by_id(meeting_id)
    if consts.CONFIRM_STORE_NOTES in context.user_data:
        del context.user_data[consts.CONFIRM_STORE_NOTES]
        if meeting is None:
            query.edit_message_text("The meeting is invalid. Please try again.")
        else:
            context.user_data[consts.STORE_NOTES] = meeting
            query.edit_message_text("Please send me the meeting notes file.")
    else:
        if meeting.notes:
            context.user_data[consts.CONFIRM_STORE_NOTES] = True
            query.edit_message_text(
                "A meeting notes file already exists for this meeting, "
                "do you want to replace it?",
                reply_markup=store_notes_confirm_keyboard(meeting_id),
            )
        else:
            context.user_data[consts.STORE_NOTES] = meeting
            query.edit_message_text("Please send me the meeting notes file.")


def get_notes_intent(update, context, intent):
    message = update.effective_message
    datetime = intent.params["datetime"]

    if datetime is not None:
        get_notes_with_datetime(message, datetime)
    else:
        get_notes_without_datetime(message)


def get_notes_with_datetime(message, datetime):
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

    reply_markup = InlineKeyboardMarkup(keyboard)
    message.reply_text(
        "Please select the meeting that you'll like to retrieve the notes.",
        reply_markup=reply_markup,
    )


def get_notes_callback(update, context):
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
