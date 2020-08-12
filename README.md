# COMP9323 Chatbot

The bot is deployed on Heroku, you can chat with [@csedojobot](https://t.me/csedojobot) on Telegram directly. Since we are running on a free tier, the app will go into sleep mode when it is inactive for a certain period of time. Therefore, the first message you send to the bot might take some time to respond.

We have also included a set of instructions below to setup and run the bot locally.

## Getting Started

The bot requires Python 3.6+ and [ffmpeg](https://ffmpeg.org/download.html) so make sure you have them installed before proceeding to the next steps.

### Install the required packages

    pip3 install -r requirements.txt

### Obtain your Telegram token

On Telegram, create a new bot with [@BotFather](https://t.me/BotFather) to obtain your bot token.

After creating your bot, you will also have to turn off Privacy mode for this bot. You can do this through [@BotFather](https://t.me/BotFather) with the `/mybots` command > Select your bot > Bot Settings > Group Privacy > Turn off.

### Setup environment file

Copy the environment file and replace `<YOUR_TELEGRAM_BOT_TOKEN>` in .env with the token you obtained from [@BotFather](https://t.me/BotFather)

    cp .env.example .env
    
### Obtain key file for authentication for Dialogflow

_NOTE THAT This step is not required with our submitted files as we have included the keyfile_

Obtain the json file for Authentication following https://cloud.google.com/docs/authentication/getting-started

Move downloaded the json file to root directory and rename to `keyfile.json`

### Initialise the database

    python3 bot.py --init_db

### Run the bot

    python3 bot.py

You can now search for your bot on Telegram and start chatting with it
.