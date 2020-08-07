import argparse
import logging
import os

from dotenv import load_dotenv
from telegram import ChatAction, ParseMode, KeyboardButton, ReplyKeyboardMarkup, Chat
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)

import consts
import dojobot
from db import DATABASE
from api_service import get_intent
from models import Users

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

    # Configure notifications job
    job_queue = updater.job_queue
    job_queue.run_repeating(send_notis, interval=10, first=0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_msg))
    dp.add_handler(CommandHandler("help", help_msg))

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, greet_group))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_msg))
    dp.add_handler(MessageHandler(Filters.document, store_document))

    # show schedule and change remind
    dp.add_handler(
        CallbackQueryHandler(dojobot.remind_main_menu, pattern="remind_main")
    )
    dp.add_handler(CallbackQueryHandler(dojobot.remind_first_menu, pattern=r"rf.*"))
    dp.add_handler(CallbackQueryHandler(dojobot.change_remind, pattern=r"cr.*"))
    dp.add_handler(
        CallbackQueryHandler(dojobot.cancel_del, pattern="cancel_change_reminder")
    )

    # show schedule and cancel meeting
    dp.add_handler(
        CallbackQueryHandler(
            dojobot.cancel_meeting_main_menu, pattern="cancel_meeting_main"
        )
    )

    dp.add_handler(
        CallbackQueryHandler(dojobot.cancel_meeting_first_menu, pattern=r"cf.*")
    )
    dp.add_handler(CallbackQueryHandler(dojobot.cancel_meeting, pattern=r"cm.*"))
    dp.add_handler(
        CallbackQueryHandler(dojobot.cancel_del, pattern="cancel_cancel_meeting")
    )

    dp.add_handler(
        CallbackQueryHandler(
            dojobot.store_agenda_callback, pattern=rf"{consts.STORE_AGENDA}.*"
        )
    )
    dp.add_handler(
        CallbackQueryHandler(
            dojobot.get_agenda_callback, pattern=rf"{consts.GET_AGENDA}.*"
        )
    )
    dp.add_handler(
        CallbackQueryHandler(
            dojobot.store_notes_callback, pattern=rf"{consts.STORE_NOTES}.*"
        )
    )
    dp.add_handler(
        CallbackQueryHandler(
            dojobot.get_notes_callback, pattern=rf"{consts.GET_NOTES}.*"
        )
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
    message = update.effective_message
    text = "Please check the reply keyboard for some of the things I can do.\n\n"

    if message.chat.type == Chat.PRIVATE:
        text += (
            "You can also add me into a group chat where I can help you "
            "to manage your group project.\n\n"
        )
    else:
        text += get_grp_help_msg(context)

    keyboard = [
        [KeyboardButton("Schedule meeting"), KeyboardButton("List meetings")],
        [KeyboardButton("Store notes"), KeyboardButton("Retrieve notes")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    message.reply_text(text, reply_markup=reply_markup)


def get_grp_help_msg(context):
    return (
        "To talk to me in group chats, either send your message that starts with "
        f"@{context.bot.username} or reply to a message that I sent."
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
            message.reply_text(get_grp_help_msg(context), quote=False)
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
    if not should_respond_message(context, message):
        return

    message.chat.send_action(ChatAction.TYPING)
    intent = get_intent(message.from_user.id, message.text)

    # if mssage for meeting scheduled is given
    if intent.all_params_present & (intent.intent == consts.SCHEDULE_MEETING):
        dojobot.schedule_meeting_intent(context, message, intent)
    elif intent.intent == consts.MEETING_REMINDER:
        dojobot.meeting_reminder_intent(context, message)
    elif intent.intent == consts.MEETING_NO_REMIDNER:
        dojobot.meeting_no_reminder_intent(context, message)
    elif intent.intent == consts.MEETING_LIST:
        dojobot.list_meetings_intent(message, intent)
    elif intent.intent == consts.STORE_AGENDA:
        dojobot.store_agenda_intent(context, message, intent)
    elif intent.intent == consts.GET_AGENDA:
        dojobot.get_agenda_intent(update, context, intent)
    elif intent.intent == consts.STORE_NOTES:
        dojobot.store_notes_intent(context, message, intent)
    elif intent.intent == consts.GET_NOTES:
        dojobot.get_notes_intent(update, context, intent)
    elif intent.intent == consts.CANCEL_REMINDER:
        dojobot.change_reminder_intent(message, intent)
    elif intent.intent == consts.CANCEL_MEETING:
        dojobot.cancel_meeting_intent(message, intent)
    else:
        message.reply_text(intent.fulfill_text)


def send_notis(context):
    notis = DATABASE.get_passed_notis()
    for noti in notis:
        context.bot.send_message(noti.chat_id, noti.text, parse_mode=ParseMode.HTML)
        if noti.doc_id is not None:
            context.bot.send_document(
                noti.chat_id, noti.doc_id, caption=noti.doc_caption
            )

        DATABASE.delete(noti)


def store_document(update, context):
    message = update.effective_message
    if not should_respond_message(context, message):
        return

    key = doc_type = None
    if consts.STORE_NOTES in context.user_data:
        key = consts.STORE_NOTES
        doc_type = "notes"
    elif consts.STORE_AGENDA in context.user_data:
        key = consts.STORE_AGENDA
        doc_type = "agenda"

    if key is not None:
        meeting = context.user_data[key]
        if doc_type == "notes":
            meeting.notes = message.document.file_id
        else:
            meeting.agenda = message.document.file_id

            # Update reminder with agenda
            if meeting.has_reminder:
                DATABASE.cancel_remind(meeting.meeting_id, message.chat.id)
                DATABASE.set_remind(meeting.meeting_id, message.chat.id)

        DATABASE.commit()
        update.effective_message.reply_text(
            f"<b>{message.document.file_name}</b> has been stored as the {doc_type} "
            f"for the meeting on <b>{meeting.formatted_datetime()}</b>",
            parse_mode=ParseMode.HTML,
        )
        del context.user_data[key]


def should_respond_message(context, message):
    """Check if bot should respond to the message

    Args:
        context (Context): the context object
        message (Message): the message object

    Returns:
        bool: whether the bot should respond
    """
    return message.chat.type == Chat.PRIVATE or (
        message.chat.type in {Chat.GROUP, Chat.SUPERGROUP}
        and (
            (
                message.text is not None
                and message.text.startswith(f"@{context.bot.username}")
            )
            or (
                message.reply_to_message is not None
                and message.reply_to_message.from_user.id == context.bot.id
            )
        )
    )


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
