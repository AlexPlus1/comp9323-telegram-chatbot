from telegram import (
    Poll,
    KeyboardButton,
    KeyboardButtonPollType,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Chat,
)
from telegram.error import Unauthorized

import consts


def vote_intent(context, message):
    if message.chat.type != Chat.PRIVATE:
        chat_id = message.from_user.id
        context.user_data[consts.VOTE] = message.chat.id
        message.reply_text("I've messaged you privately to create a poll.")
    else:
        chat_id = message.chat.id

    keyboard = [
        [
            KeyboardButton(
                "Create poll", request_poll=KeyboardButtonPollType(type=Poll.REGULAR)
            )
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, selective=True, resize_keyboard=True
    )

    try:
        context.bot.send_message(
            chat_id,
            "You can press the button below to create your own poll",
            reply_markup=reply_markup,
        )
    except Unauthorized:
        message.reply_text(
            "I couldn't message your privately, "
            f"please start a chat with @{context.bot.username}"
        )


def handle_received_poll(update, context):
    poll = update.effective_message.poll
    chat_id = context.user_data.get(consts.VOTE)

    if chat_id is not None:
        message = context.bot.send_poll(
            chat_id,
            question=poll.question,
            options=[x.text for x in poll.options],
            is_anonymous=poll.is_anonymous,
            allows_multiple_answers=poll.allows_multiple_answers,
        )
        context.bot_data[message.poll.id] = {
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "answers": 0,
        }
        update.effective_message.reply_text(
            "I've created the poll in your group chat.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        update.effective_message.reply_text(
            "A new poll has been created", reply_markup=ReplyKeyboardRemove()
        )


def receive_poll_answer(update, context):
    if update.poll_answer is not None:
        poll_id = update.poll_answer.poll_id
    else:
        poll_id = update.poll.id

    poll_dict = context.bot_data.get(poll_id)
    if poll_dict is not None:
        chat_id = context.bot_data[poll_id]["chat_id"]
        message_id = context.bot_data[poll_id]["message_id"]
        context.bot_data[poll_id]["answers"] += 1
        num_members = context.bot.get_chat_members_count(chat_id) - 1

        if num_members == context.bot_data[poll_id]["answers"]:
            context.bot.stop_poll(chat_id, message_id)
            context.bot.send_message(
                chat_id,
                text=(
                    "Looks like everyone in the group has voted, be sure to "
                    "take action from the results."
                ),
                reply_to_message_id=message_id,
            )
            del context.bot_data[poll_id]
