from telegram import Chat, ForceReply


def edit_query_message(context, query, text):
    """Edit query message by deleting it and sending a new one

    Args:
        context (Context): the Telegram context object
        query (CallbackQuery): the Telegram callback query object
        text (str): the message text
    """
    reply_markup = None
    if query.message.chat.type != Chat.PRIVATE:
        reply_markup = ForceReply()

    context.bot.delete_message(query.message.chat.id, query.message.message_id)
    context.bot.send_message(query.message.chat.id, text, reply_markup=reply_markup)
