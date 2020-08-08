# import consts
from db import DATABASE
from models import Tasks

from telegram.ext import ConversationHandler
import arrow

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    # KeyboardButton,
    # ParseMode,
    ReplyKeyboardMarkup,
    # ReplyKeyboardRemove,
)


def create_new_task_one(context,  update):
# def create_new_task_one(context, message, intent, update):
    user_data = context.user_data

    # temp = datetime.isoformat()
    user_data["have_task"] = 1
    user_data["new_task"] = 1
    text1 = "I want to create a task task."
    text2 = "I don`t want to create a task."
    keyboard = [
            [InlineKeyboardButton(text1, callback_data="input_task")],
            [InlineKeyboardButton(text2, callback_data="cancel_creat_task")]]
    # message.reply_text("What's the name of your task?")
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
            text="Do you want to create a new task?",
            reply_markup=reply_markup,
        )
    return ConversationHandler.END


def new_task_one(update, context):
    message = update.effective_message
    reply_keyboard = [['/edit_task'], ['/Create_task']]
    task_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    message.reply_text("if you want to assign the task, you can click '/edit_task'", reply_markup=task_markup)
    return ConversationHandler.END


def new_task_two(update, context):  
    text1 = "edit the name of the task."
    text2 = "edit the status of the task."
    text3 = "edit the summary of the task."
    text4 = "I don`t want to create a task."
    keyboard = [
            [InlineKeyboardButton(text1, callback_data="name_task")],
            [InlineKeyboardButton(text2, callback_data="status_task")],
            [InlineKeyboardButton(text3, callback_data="summary_task")],
            [InlineKeyboardButton(text4, callback_data="cancel_creat_task")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Please input information of the task!",
        reply_markup=reply_markup)


def input_name_task(update, context):
    query = update.callback_query
    query.answer()
    user_data = context.user_data
    if user_data.get("have_task"):
        user_data["edit_name_task"] = 1
        temp_text = "Please input the name of the task！"      
    else:
        temp_text = "Please select a task!"
    query.edit_message_text(
            text=temp_text,
        ) 
    return ConversationHandler.END
    
    
def input_status_task(update, context):
    query = update.callback_query
    query.answer()
    user_data = context.user_data
    if user_data.get("have_task"):
        user_data["edit_status_task"] = 1
        temp_text = "Please input the status of the task！"      
    else:
        temp_text = "Please select a task!"
    query.edit_message_text(
            text=temp_text,
        ) 
    return ConversationHandler.END
    

def input_summary_task(update, context):
    query = update.callback_query
    query.answer()
    user_data = context.user_data
    if user_data.get("have_task"):
        user_data["edit_summary_task"] = 1
        temp_text = "Please input the summary of the task！"      
    else:
        temp_text = "Please select a task!"
    query.edit_message_text(
            text=temp_text,
        ) 
    return ConversationHandler.END


def cancel_creat_task(update, context):
    user_data = context.user_data
    del user_data["have_task"]
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="What else can I do for you?")
    return ConversationHandler.END


def task_done(update, context):
    user_data = context.user_data
    if user_data.get("have_task"):
        if user_data.get("new_task"):
            temp_task = user_data["cur_task"]
            DATABASE.insert(temp_task)
            update.message.reply_text("done",)
            update.message.reply_text(f"task name:{temp_task.name}",)
            update.message.reply_text(f"task due:{temp_task.due_date}",)
            update.message.reply_text(f"task status:{temp_task.status}",)
            update.message.reply_text(f"task summary:{temp_task.summary}",)
    del user_data["have_task"]
    del user_data["new_task"]
    del user_data["cur_task"]
    return ConversationHandler.END


def list_tasks_intent(update, message, intent):
    pass
