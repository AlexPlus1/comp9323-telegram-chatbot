import argparse
import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatAction,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)
import arrow

import consts
from api_service import get_intent
from models import Database, Teams, Meetings

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE = Database()


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
    
    job = updater.job_queue
    job.run_repeating(check_meeting_reminder, interval=300, first=0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_callback_query))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, greet_group))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_msg))
    dp.add_handler(MessageHandler(Filters.document, store_meeting_notes))
    
    #show schedule and change remind
    dp.add_handler(CallbackQueryHandler(remind_main_menu, pattern='remind_main'))
    #dp.add_handler(CallbackQueryHandler(remind_first_menu, pattern='remind_sub'))

    dp.add_handler(CallbackQueryHandler(remind_first_menu, pattern=r'rf.*'))
    dp.add_handler(CallbackQueryHandler(change_remind, pattern=r'cr.*'))
    # dp.add_handler(CallbackQueryHandler(cancel_redmind, pattern=r'cr.*'))
    # dp.add_handler(CallbackQueryHandler(set_redmind, pattern=r'sr.*'))                                                    
    dp.add_handler(CallbackQueryHandler(cancel_del,pattern='cancel_change_reminder'))


    # Start the Bot
    updater.start_polling()
    LOGGER.info("Bot started polling")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def start(update, context):
    update.message.reply_text(
        f"Hi! I'm {consts.BOT_NAME}. Add me into a group chat to get started"
    )


def greet_group(update, context):
    message = update.effective_message
    for user in message.new_chat_members:
        if user.id == context.bot.id:
            chat_id = message.chat.id
            team = DATABASE.get_team(chat_id)

            if team is None:
                team = Teams(team_id=chat_id)
                DATABASE.insert(team)

            context.bot.send_message(
                chat_id,
                f"Hello everyone! I'm {consts.BOT_NAME} and I've initialised a team for this group chat.",
            )


def handle_text_msg(update, context):
    message = update.effective_message
    message.chat.send_action(ChatAction.TYPING)
    # init the team
    chat_id = message.chat.id
    team = DATABASE.get_team(chat_id)
    if team is None:
        team = Teams(team_id=chat_id)
        DATABASE.insert(team)

    intent = get_intent(message.from_user.id, message.text)

    # if mssage for meeting scheduled is given
    if intent.all_params_present & (intent.intent == consts.SCHEDULE_MEETING):
        if intent.params["datetime"] < arrow.now():
            message.reply_text("Can't schedule a meeting in the past")
        else:
            end = intent.params["datetime"].shift(
                minutes=int(intent.params["duration"])
            )
            # meetings = DATABASE.get_all_meetings()
            meetings = DATABASE.get_all_meetings(chat_id)
            sign = 0
            if meetings:
                for meeting in meetings:
                    tmp_start = meeting.datetime
                    tmp_end = tmp_start.shift(minutes=meeting.duration)
                    if end <= tmp_start:
                        continue
                    elif intent.params["datetime"] >= tmp_end:
                        continue
                    else:
                        sign = 1
                        tmp_time = tmp_start.to("local").format("YYYY-MM-DD HH:mm ZZZ")
                        message.reply_text(
                            "Can't schedule this meeting, time conflicting with meeting at {} lasting for {} minutes".format(
                                tmp_time, meeting.duration
                            )
                        )
                        break
            if sign == 0:
                time = intent.params["datetime"].format("YYYY-MM-DD HH:mm ZZZ")
                reply = "Your meeting has been scheduled on {} for {} minutes.\nReminder: {}".format(
                    time, int(intent.params["duration"]), intent.params["reminder"]
                )
                if intent.params["reminder"] == "on":
                    tmp_v = True
                else:
                    tmp_v = False
                new_meeting = Meetings(
                    datetime=intent.params["datetime"].to("UTC"),
                    duration=int(intent.params["duration"]),
                    has_reminder=tmp_v,
                    notes="",
                    teams=team,
                )
                DATABASE.insert(new_meeting)
                message.reply_text(reply)
    elif intent.intent == consts.MEETING_LIST:
        meetings = DATABASE.get_all_meetings(chat_id)
        reply = intent.fulfill_text
        if meetings:
            i = 1
            for meeting in meetings:
                time = meeting.datetime.to("local").format("YYYY-MM-DD HH:mm ZZZ")
                tmp = "\n{}: {} for {} minutes".format(i, time, meeting.duration)
                reply += tmp
                i += 1
            message.reply_text(reply)
        else:
            message.reply_text("There's no upcoming meetings")
    elif intent.intent == consts.STORE_MEETING_NOTES and intent.all_params_present:
        handle_store_notes_intent(update, context, intent)
    elif intent.intent == consts.GET_MEETING_NOTES and intent.all_params_present:
        get_meeting_notes(update, context, intent)
    elif intent.intent == consts.CANCEL_REMINDER:
        update.message.reply_text( text='Choose the option in main menu:',
                            reply_markup=remind_main_menu_keyboard())
    else:
        message.reply_text(intent.fulfill_text)

###############################  REMINDER ############################################
def check_meeting_reminder(context: CallbackContext):
    meetings = DATABASE.get_all_my_meetings()
    for m in meetings :
        if m.has_reminder == True:
            temp_time = arrow.get(m.datetime)
            cur_time =  arrow.utcnow()
            range = temp_time - cur_time
            if  86400 <= range.seconds < 86700:          
                context.bot.send_message(chat_id=m.teams_id, 
                                text='Your meeting will start in 24 hours!')
            elif  3600 <= range.seconds < 3900:     
            #elif  300 <= range.seconds < 340:       
                context.bot.send_message(chat_id=m.teams_id, 
                                text='Your meeting will start in an hour!')
            elif 300 <= range.seconds < 600:
            #elif 0 <= range.seconds < 299:
                context.bot.send_message(chat_id=m.teams_id, 
                                text='Your meeting will start soon!')
                                
def change_remind(update,context):

    query = update.callback_query
    temp = query.data[2:]
    query.answer()
    check = DATABASE.reminder_state(temp)
    if check == True:
        temp_text = "You have cancelled the reminder!"
        DATABASE.cancel_remind(temp)      
    else:
        temp_text = "You have set the reminder!"    
        DATABASE.set_remind(temp)
        
    query.edit_message_text(
        text = temp_text
    )
    return ConversationHandler.END
    
def cancel_del(update,context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="What else can I do for you?"
    )
    return ConversationHandler.END                       
       
 ###############################  MENU ############################################

def remind_main_menu(update,context):
    
    query = update.callback_query
    query.answer()
    query.edit_message_text(
                        text='Choose the meeting:',
                        reply_markup=remind_main_menu_keyboard())

def remind_main_menu_keyboard():  
    meetings = DATABASE.get_all_my_meetings()
    keyboard = []
    for meeting in meetings:
        temp = meeting.datetime.to("local").format("YYYY-MM-DD HH:mm ZZZ")
        keyboard.append([InlineKeyboardButton(temp, callback_data=f"rf{meeting.meeting_id}")]) 
    keyboard.append([InlineKeyboardButton("I dont want to change reminder", callback_data="cancel_change_reminder")]) 
    return InlineKeyboardMarkup(keyboard)

def remind_first_menu(update,context):
    query = update.callback_query
    query.answer()
    temp = query.data[2:]
    check = DATABASE.reminder_state(temp)
    if check == True:
        reminder = "reminider state: on"
    else:
        reminder = "reminider state: off"
    query.edit_message_text(
                        text=reminder,
                        reply_markup=remind_first_menu_keyboard(temp))
                        
def remind_first_menu_keyboard(temp):
    keyboard = [[InlineKeyboardButton('cancel reminder', callback_data=f"cr{temp}")],
            [InlineKeyboardButton('set reminder', callback_data=f"cr{temp}")],
            [InlineKeyboardButton('schedules', callback_data="remind_main")]]
    return InlineKeyboardMarkup(keyboard)
            

def handle_store_notes_intent(update, context, intent):
    message = update.effective_message
    datetime = intent.params["datetime"]
    meeting = DATABASE.get_meeting_by_time(message.chat_id, datetime)

    if meeting is None:
        message.reply_text(
            "No meeting found with the given date and time. Please try again."
        )
    else:
        if meeting.notes:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Yes",
                        callback_data=f"{consts.STORE_MEETING_NOTES},{datetime.format()}",
                    ),
                    InlineKeyboardButton(
                        "No", callback_data=f"{consts.STORE_MEETING_NOTES},no",
                    ),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message.reply_text(
                "A meeting notes file already exists for this meeting, do you want to replace it?",
                reply_markup=reply_markup,
            )
        else:
            context.user_data[consts.STORE_MEETING_NOTES] = meeting
            message.reply_text(intent.fulfill_text)


def store_meeting_notes(update, context):
    if consts.STORE_MEETING_NOTES in context.user_data:
        message = update.effective_message
        meeting = context.user_data[consts.STORE_MEETING_NOTES]
        meeting.notes = message.document.file_id
        DATABASE.commit()
        update.effective_message.reply_text(
            f"{message.document.file_name} has been stored as the notes for the meeting on {meeting.formatted_datetime()}"
        )
        del context.user_data[consts.STORE_MEETING_NOTES]


def get_meeting_notes(update, context, intent):
    message = update.effective_message
    datetime = intent.params["datetime"]
    meeting = DATABASE.get_meeting_by_time(message.chat_id, datetime)

    if meeting is None:
        message.reply_text(
            "No meeting found with the given date and time. Please try again."
        )
    else:
        if meeting.notes:
            message.reply_document(meeting.notes, caption="Here's your meeting notes.")
        else:
            message.reply_text("No meeting notes found for the meeting.")


def handle_callback_query(update, context):
    query = update.callback_query
    query.answer()
    intent, data = query.data.split(",")

    if intent == consts.STORE_MEETING_NOTES:
        handle_store_notes_callback(context, query, data)


def handle_store_notes_callback(context, query, data):
    if data == "no":
        query.edit_message_text("Cancelled for storing meeting notes")
    else:
        datetime = arrow.get(data)
        meeting = DATABASE.get_meeting_by_time(query.message.chat_id, datetime)

        if meeting is None:
            query.edit_message_text("The meeting is invalid. Please try again.")
        else:
            context.user_data[consts.STORE_MEETING_NOTES] = meeting
            query.edit_message_text("Please send me the meeting notes file.")


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
