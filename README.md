# COMP9323 Chatbot

## Getting Started

### Install the required packages

    pip3 install -r requirements.txt

### Obtain your Telegram token

On Telegram, create a new bot with [@BotFather](https://t.me/BotFather) to obtain your bot token

### Setup environment file

Copy the environment file and replace `<YOUR_TELEGRAM_BOT_TOKEN>` in .env with the token you obtained from @BotFather

    cp .env.example .env
    
### Obtain keyfile.json for authentication for Dialogflow

_This step is not required with our submitted files as we have included the keyfile_

Obtain .json file for Authentication following https://cloud.google.com/docs/authentication/getting-started

Move downloaded .json file to root directory and rename to keyfile.json

### Initialise the database

    python3 bot.py --init_db

### Run the bot

    python3 bot.py

You can now search for your bot on Telegram and start chatting with it
