from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler

from db import DATABASE


def change_reminder_intent(message, intent):
    datetime = intent.params["datetime"]
    if datetime is not None:
        meeting = DATABASE.get_meeting_by_time(message.chat.id, datetime)
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
                [InlineKeyboardButton(button, callback_data=f"cr{meeting.meeting_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message.reply_text(
                text=f"Reminder is currently <b>turned {status}</b>",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )
    else:
        message.reply_text(
            text="Choose the option in main menu:",
            reply_markup=remind_main_menu_keyboard(),
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


# ---------------------------------------- MENU ----------------------------------------
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
