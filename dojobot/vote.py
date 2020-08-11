from telegram import Poll, KeyboardButton, KeyboardButtonPollType, ReplyKeyboardMarkup, ReplyKeyboardRemove

def vote_intent(message):
    keyboard = [[
        KeyboardButton(
            "Create poll",
            request_poll=KeyboardButtonPollType(type=Poll.REGULAR)
        )
    ]]

    message.reply_text(
        "You can press the button below to create your own poll",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            selective=True
        )
    )

def vote_keyboard_remove(update, context):
    update.effective_message.reply_text(
        "A new poll has been created",
        reply_markup=ReplyKeyboardRemove()
    )
