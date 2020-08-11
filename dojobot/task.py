from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Chat

import consts

from db import DATABASE
from models import Tasks


def create_task_intent(context, message, intent):
    task = Tasks(team=DATABASE.get_team(message.chat_id), status=consts.TASK_TODO)
    context.user_data[consts.CURR_TASK] = task
    ask_task_details(message, task)


def ask_task_details(message, task):
    keyboard = [
        [
            InlineKeyboardButton("Name", callback_data=consts.EDIT_TASK_NAME),
            InlineKeyboardButton("Summary", callback_data=consts.EDIT_TASK_SUMMARY),
            InlineKeyboardButton("Status", callback_data=consts.EDIT_TASK_STATUS),
        ],
        [
            InlineKeyboardButton("Due Date", callback_data=consts.EDIT_TASK_DATE),
            InlineKeyboardButton("Assigner", callback_data=consts.EDIT_TASK_USER),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data=consts.CANCEL_CREATE_TASK),
            InlineKeyboardButton("Done", callback_data=consts.CREATE_TASK_DONE),
        ],
    ]

    text = get_task_text(task)
    text += "\n\nPlease select from below the task field you'll like to edit"
    reply_markup = InlineKeyboardMarkup(keyboard)
    message.reply_text(
        text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML,
    )


def get_task_text(task):
    assignee = None
    if task.user_id is not None:
        user = DATABASE.get_user(task.user_id)
        assignee = user.name

    return (
        f"Name: <b>{task.name}</b>\nSummary: <b>{task.summary}</b>\n"
        f"Status: <b>{task.status}</b>\nDue Date: <b>{task.formatted_date()}</b>\n"
        f"Assignee: <b>{assignee}</b>"
    )


def ask_task_name(update, context):
    query = update.callback_query
    query.answer()

    if context.user_data.get(consts.CURR_TASK) is not None:
        context.user_data[consts.EDIT_TASK_NAME] = True
        text = "Please tell me the task name."
    else:
        text = "Invalid task, please try again."

    query.edit_message_text(text,)


def ask_task_summary(update, context):
    query = update.callback_query
    query.answer()

    if context.user_data.get(consts.CURR_TASK) is not None:
        context.user_data[consts.EDIT_TASK_SUMMARY] = True
        text = "Please tell me the task summary."
    else:
        text = "Invalid task, please try again."

    query.edit_message_text(text)


def ask_task_status(update, context):
    query = update.callback_query
    query.answer()
    reply_markup = None

    if context.user_data.get(consts.CURR_TASK) is not None:
        keyboard = [
            [
                InlineKeyboardButton(
                    consts.TASK_TODO,
                    callback_data=f"{consts.SET_TASK_STATUS},{consts.TASK_TODO}",
                ),
                InlineKeyboardButton(
                    consts.TASK_DOING,
                    callback_data=f"{consts.SET_TASK_STATUS},{consts.TASK_DOING}",
                ),
                InlineKeyboardButton(
                    consts.TASK_DONE,
                    callback_data=f"{consts.SET_TASK_STATUS},{consts.TASK_DONE}",
                ),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Please select the task status."
    else:
        text = "Invalid task, please try again."

    query.edit_message_text(text, reply_markup=reply_markup)


def task_status_callback(update, context):
    query = update.callback_query
    query.answer()
    task = context.user_data.get(consts.CURR_TASK)
    _, status = query.data.split(",")

    if task is not None:
        task.status = status
        context.bot.delete_message(query.message.chat.id, query.message.message_id)
        ask_task_details(query.message, task)
    else:
        query.edit_message_text("Invalid task, please try again.")


def ask_task_date(update, context):
    query = update.callback_query
    query.answer()

    if context.user_data.get(consts.CURR_TASK) is not None:
        context.user_data[consts.EDIT_TASK_DATE] = True
        text = "Please tell me the task due date."
    else:
        text = "Invalid task, please try again."

    query.edit_message_text(text)


def ask_task_user(update, context):
    query = update.callback_query
    query.answer()
    reply_markup = None

    if context.user_data.get(consts.CURR_TASK) is not None:
        keyboard = []
        reply_markup = None
        if query.message.chat.type == Chat.PRIVATE:
            from_user = query.from_user
            name = from_user.first_name

            if from_user.username is not None:
                name = from_user.username

            keyboard.append(
                [
                    InlineKeyboardButton(
                        name,
                        callback_data=(f"{consts.SET_TASK_USER},{query.from_user.id}"),
                    )
                ]
            )
        else:
            users = DATABASE.get_users(query.message.chat.id)
            for user in users:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            user.name,
                            callback_data=(f"{consts.SET_TASK_USER},{user.user_id}"),
                        )
                    ]
                )

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Please select the Assigner."
    else:
        text = "Invalid task, please try again."

    query.edit_message_text(text, reply_markup=reply_markup)


def task_user_callback(update, context):
    query = update.callback_query
    query.answer()
    _, user_id = query.data.split(",")
    task = context.user_data.get(consts.CURR_TASK)

    if task is not None:
        task.user_id = user_id
        context.bot.delete_message(query.message.chat.id, query.message.message_id)
        ask_task_details(query.message, task)
    else:
        query.edit_message_text("Invalid task, please try again.")


def cancel_create_task(update, context):
    if consts.CURR_TASK in context.user_data:
        del context.user_data[consts.CURR_TASK]

    query = update.callback_query
    query.answer()
    query.edit_message_text("What else can I do for you?")


def create_task(update, context):
    query = update.callback_query
    query.answer()
    task = context.user_data.get(consts.CURR_TASK)
    is_task_created = False

    if task is None:
        text = "Invalid task, please try again."
    else:
        if task.name is None:
            text = "Task name is required, please set the task name."
        else:
            if task.task_id is None:
                operation = "created"
                DATABASE.insert(task)
            else:
                operation = "updated"
                DATABASE.set_task(task.task_id, task)
                DATABASE.commit()

            is_task_created = True
            text = f"I've {operation} the following task."
            del context.user_data[consts.CURR_TASK]

    query.edit_message_text(text)
    if task is not None and not is_task_created:
        ask_task_details(query.message, task)
    elif is_task_created:
        context.bot.send_message(
            query.message.chat.id, get_task_text(task), parse_mode=ParseMode.HTML
        )


def list_tasks_intent(update, message, intent):
    tasks = DATABASE.get_tasks(message.chat_id)
    reply = intent.fulfill_text + "\n"
    i = 1

    for task in tasks:
        tmp = "\n{}: {} ".format(i, get_task_text(task))
        reply += tmp
        i += 1

    if tasks:
        message.reply_text(reply, parse_mode=ParseMode.HTML)
    else:
        message.reply_text("There's no task, considering create one?")

def list_mine_tasks_intent(update, message, intent):
    tasks = DATABASE.get_tasks_by_user(message.from_user.id)
    reply = intent.fulfill_text + "\n"
    i = 1

    for task in tasks:
        tmp = "\n{}: {} ".format(i, get_task_text(task))
        reply += tmp
        i += 1

    if tasks:
        message.reply_text(reply, parse_mode=ParseMode.HTML)
    else:
        message.reply_text("There's no your task, considering create one?")


def update_task_intent(message):
    tasks = DATABASE.get_tasks(message.chat.id)
    keyboard = []

    for task in tasks:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{task.name} ({task.status})",
                    callback_data=f"{consts.UPDATE_TASK},{task.task_id}",
                )
            ]
        )

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text(
            "Please select the task to update:", reply_markup=reply_markup
        )
    else:
        message.reply_text("You don't have any tasks.")


def update_task_callback(update, context):
    query = update.callback_query
    query.answer()
    _, task_id = query.data.split(",")
    task = DATABASE.get_task(task_id)

    if task is not None:
        context.bot.delete_message(query.message.chat.id, query.message.message_id)
        context.user_data[consts.CURR_TASK] = task
        ask_task_details(query.message, task)
    else:
        query.edit_message_text("Invalid task, please try again.")
