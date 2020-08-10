# COMP9323 Chatbot

## Getting Started

### Install the required packages

    pip3 install requirements.txt

### Obtain your Telegram token

On Telegram, create a new bot with [@BotFather](https://t.me/BotFather) to obtain your bot token

### Setup environment file

Copy the environment file and replace the `TELEGRAM_TOKEN` with the token you obtained above

    cp .env.example .env

### Initialise the database

    python bot.py --init_db

### Run the bot

    python3 bot.py

You can now search for your bot on Telegram and start chatting with it