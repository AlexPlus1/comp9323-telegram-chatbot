from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Chat,
)
from telegram.error import Unauthorized

import consts

from db import database
from models import Tasks
from dojobot import utils


def create_task_intent(context, message, intent):
    """Handle create task intent

    Args:
        context (Context): the Telegram context object
        message (Message): the Telegram message object
        intent (IntentResult): the intent result from Dialogflow
    """
    task = Tasks(team_id=message.chat_id, status=consts.TASK_TODO)
    context.user_data[consts.CURR_TASK] = task
    ask_task_details(context.bot, message.chat_id, task)


def ask_task_details(bot, chat_id, task):
    """Ask for the task details to create or update a task

    Args:
        bot (Bot): the Telegram bot object
        chat_id (int): the chat ID
        task (Task): the Task object
    """
    keyboard = [
        [
            InlineKeyboardButton("Name", callback_data=consts.EDIT_TASK_NAME),
            InlineKeyboardButton("Summary", callback_data=consts.EDIT_TASK_SUMMARY),
            InlineKeyboardButton("Status", callback_data=consts.EDIT_TASK_STATUS),
        ],
        [
            InlineKeyboardButton("Due Date", callback_data=consts.EDIT_TASK_DATE),
            InlineKeyboardButton("Assignee", callback_data=consts.EDIT_TASK_USER),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data=consts.CANCEL_CREATE_TASK),
            InlineKeyboardButton("Done", callback_data=consts.CREATE_TASK_DONE),
        ],
    ]

    text = get_task_text(task)
    text += "\n\nPlease select from below the task field you'll like to edit"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
    )


def get_task_text(task):
    """Format all the task fields into a string

    Args:
        task (Task): the Task object

    Returns:
        str: the task details
    """
    assignee = None
    if task.user_id is not None:
        user = database.get_user(task.user_id)
        assignee = user.name

    return (
        f"Name: <b>{task.name}</b>\nSummary: <b>{task.summary}</b>\n"
        f"Status: <b>{task.status}</b>\nDue Date: <b>{task.formatted_date()}</b>\n"
        f"Assignee: <b>{assignee}</b>"
    )


def ask_task_name(update, context):
    """Ask user for the task name

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()

    if context.user_data.get(consts.CURR_TASK) is not None:
        context.user_data[consts.EDIT_TASK_NAME] = True
        text = "Please tell me the task name."
    else:
        text = "Invalid task, please try again."

    utils.edit_query_message(context, query, text)


def ask_task_summary(update, context):
    """Ask user for the task summary

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()

    if context.user_data.get(consts.CURR_TASK) is not None:
        context.user_data[consts.EDIT_TASK_SUMMARY] = True
        text = "Please tell me the task summary."
    else:
        text = "Invalid task, please try again."

    utils.edit_query_message(context, query, text)


def ask_task_status(update, context):
    """Ask user for the task status

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
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
    """Handle user selected a task status

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    task = context.user_data.get(consts.CURR_TASK)
    _, status = query.data.split(",")

    if task is not None:
        task.status = status
        context.bot.delete_message(query.message.chat.id, query.message.message_id)
        ask_task_details(context.bot, query.message.chat_id, task)
    else:
        query.edit_message_text("Invalid task, please try again.")


def ask_task_date(update, context):
    """Ask user for the task due date

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()

    if context.user_data.get(consts.CURR_TASK) is not None:
        context.user_data[consts.EDIT_TASK_DATE] = True
        text = "Please tell me the task due date."
    else:
        text = "Invalid task, please try again."

    utils.edit_query_message(context, query, text)


def ask_task_user(update, context):
    """Ask user for the user to assign this task to

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    reply_markup = None
    task = context.user_data.get(consts.CURR_TASK)

    if task is not None:
        keyboard = []
        reply_markup = None

        # There's only one user in private chats
        if query.message.chat.type == Chat.PRIVATE:
            from_user = query.from_user
            name = from_user.first_name

            if from_user.username is not None:
                name = from_user.username

            keyboard.append(
                [
                    InlineKeyboardButton(
                        name,
                        callback_data=f"{consts.SET_TASK_USER},{query.from_user.id}",
                    )
                ]
            )

        # Get all users in the group chat
        else:
            users = database.get_users(query.message.chat.id)
            for user in users:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            user.name,
                            callback_data=f"{consts.SET_TASK_USER},{user.user_id}",
                        )
                    ]
                )

        # If task has been assigned, add option to remove assignee
        if task.user_id is not None:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "Remove Assignee",
                        callback_data=f"{consts.SET_TASK_USER},remove",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Please select the task assignee."
    else:
        text = "Invalid task, please try again."

    query.edit_message_text(text, reply_markup=reply_markup)


def task_user_callback(update, context):
    """Handle user selected a user to assign the task

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    _, user_id = query.data.split(",")
    task = context.user_data.get(consts.CURR_TASK)

    if user_id == "remove":
        user_id = None

    if task is not None:
        context.user_data[consts.ASSIGNEE_CHANGE] = task.user_id != user_id
        task.user_id = user_id
        context.bot.delete_message(query.message.chat.id, query.message.message_id)
        ask_task_details(context.bot, query.message.chat_id, task)
    else:
        query.edit_message_text("Invalid task, please try again.")


def cancel_create_task(update, context):
    """Cancel the create or update task workflow

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    if consts.CURR_TASK in context.user_data:
        del context.user_data[consts.CURR_TASK]

    query = update.callback_query
    query.answer()
    query.edit_message_text("What else can I do for you?")


def create_task(update, context):
    """Create or update a task

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    task = context.user_data.get(consts.CURR_TASK)
    is_task_created = is_task_updated = is_assignee_changed = is_task_done = False

    if task is None:
        text = "Invalid task, please try again."
    else:
        if task.name is None:
            text = "Task name is required, please set the task name."
        else:
            if task.task_id is None:
                is_task_created = True
                operation = "created"
                database.insert(task)
            else:
                is_task_updated = True
                operation = "updated"
                task = database.set_task(task.task_id, task)

            if consts.ASSIGNEE_CHANGE in context.user_data:
                is_assignee_changed = context.user_data[consts.ASSIGNEE_CHANGE]
                del context.user_data[consts.ASSIGNEE_CHANGE]

            is_task_done = task.status == consts.TASK_DONE
            text = f"I've {operation} the following task."
            del context.user_data[consts.CURR_TASK]

    query.edit_message_text(text)

    if task is not None:
        # Task is invalid, ask user to update its details again
        if not is_task_created and not is_task_updated:
            ask_task_details(context.bot, query.message.chat_id, task)
        else:
            task_text = get_task_text(task)
            context.bot.send_message(
                query.message.chat.id, task_text, parse_mode=ParseMode.HTML
            )

            # Send the created task to the assignee privately
            if (
                (is_task_created or is_assignee_changed)
                and query.message.chat.type != Chat.PRIVATE
                and task.user_id is not None
            ):
                group = context.bot.get_chat(task.team_id).title
                text = (
                    f"You've been assigned to this task in '{group}':\n\n" + task_text
                )

                try:
                    context.bot.send_message(
                        task.user_id, text, parse_mode=ParseMode.HTML
                    )
                except Unauthorized:
                    pass

        # Task has been updated to done, ask for task feedback and give suggestion
        if is_task_done:
            if task.user_id is not None:
                ask_task_feedback(context.bot, query.message.chat.id, task)

            task_done_suggest(context.bot, query.message.chat.id, query.from_user.id)


def list_tasks_intent(update, message):
    """Handle list tasks intent

    Args:
        update (Update): the Telegram update object
        message (Message): the Telegram message object
    """
    tasks = database.get_tasks(message.chat_id)
    if tasks:
        reply_markup = get_tasks_keyboard(tasks)
        message.reply_text(
            text=(
                "Please see below for all your tasks and "
                "click onto them to view their details/update them."
            ),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        message.reply_text("You haven't created any tasks.")


def list_mine_tasks_intent(update, message):
    """Handle list user assigned tasks

    Args:
        update (Update): the Telegram update object
        message (Message): the Telegram message object
    """
    tasks = database.get_tasks_by_user(message.chat.id, message.from_user.id)
    if tasks:
        reply_markup = get_tasks_keyboard(tasks)
        message.reply_text(
            text=(
                "Please see below for all the tasks assigned to you and "
                "click on them to view their details/update them."
            ),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    else:
        message.reply_text("You don't have any assigned tasks.")


def update_task_intent(message):
    """Handle update task intent

    Args:
        message (Message): the Telegram message object
    """
    tasks = database.get_tasks(message.chat.id)
    if tasks:
        reply_markup = get_tasks_keyboard(tasks)
        message.reply_text(
            "Please select the task to update:", reply_markup=reply_markup
        )
    else:
        message.reply_text("You don't have any tasks.")


def update_task_callback(update, context):
    """User has selected a task to update, ask for the new task details

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    _, task_id = query.data.split(",")
    task = database.get_task(task_id)

    if task is not None:
        context.bot.delete_message(query.message.chat.id, query.message.message_id)
        context.user_data[consts.CURR_TASK] = task
        ask_task_details(context.bot, query.message.chat_id, task)
    else:
        query.edit_message_text("Invalid task, please try again.")


def ask_task_feedback(bot, chat_id, task):
    """Ask users to provide feedback on a completed task

    Args:
        bot (Bot): the Telegram bot object
        chat_id (int): the chat ID
        task (Task): the Task object
    """
    keyboard = []
    for feeback_type, emoji in consts.FEEDBACK_TYPES.items():
        keyboard.append(
            InlineKeyboardButton(
                f"{emoji} 0",
                callback_data=f"{consts.TASK_FEEDBACK},{task.task_id},{feeback_type}",
            )
        )

    reply_markup = InlineKeyboardMarkup([keyboard])
    bot.send_message(
        chat_id,
        text=(f"{task.user.name} has completed <b>{task.name}</b>, Great job!"),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


def task_feedback_callback(update, context):
    """Handle user providing task feedback

    Args:
        update (Update): the Telegram update object
        context (Context): the Telegram context object
    """
    query = update.callback_query
    query.answer()
    _, task_id, user_feedback = query.data.split(",")
    task = database.get_task(task_id)

    if task is not None:
        database.add_feedback(task.task_id, query.from_user.id, user_feedback)
        keyboard = []

        for feedback_type, emoji in consts.FEEDBACK_TYPES.items():
            count = database.get_feedback_count(task_id, feedback_type)
            keyboard.append(
                InlineKeyboardButton(
                    f"{emoji} {count}",
                    callback_data=(
                        f"{consts.TASK_FEEDBACK},{task.task_id},{feedback_type}"
                    ),
                )
            )

        reply_markup = InlineKeyboardMarkup([keyboard])
        query.edit_message_reply_markup(reply_markup)


def task_done_suggest(bot, chat_id, user_id):
    """Suggest user for next steps after task completion

    Args:
        bot (Bot): the Telegram bot object
        chat_id (int): the chat ID
        user_id (int): the user ID
    """
    reply_markup = None
    tasks = database.get_tasks_by_user(chat_id, user_id, status=consts.TASK_TODO)

    # Check for to-do tasks assigned to the user
    if tasks:
        text = (
            "Here are the To-Do tasks assigned to you, consider to "
            "work on one of these tasks next:"
        )
        reply_markup = get_tasks_keyboard(tasks)
    else:
        # Check for to-do tasks for the team
        tasks = database.get_tasks(chat_id, status=consts.TASK_TODO)
        if tasks:
            text = (
                "Here are the To-Do tasks for the team, consider to "
                "work on one of these tasks next:"
            )
            reply_markup = get_tasks_keyboard(tasks)
        else:
            text = (
                "There's no more To-Do tasks for your team. "
                "Keep working on the remaining Doing tasks or "
                "schedule another meeting about next steps."
            )

    bot.send_message(chat_id, text, reply_markup=reply_markup)


def get_tasks_keyboard(tasks):
    """Get the tasks keyboard

    Args:
        tasks (list): the list of tasks

    Returns:
        InlineKeyboardMarkup: the tasks keyboard
    """
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

    return InlineKeyboardMarkup(keyboard)
