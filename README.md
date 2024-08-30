This is the telegram bot that can summarize n last messages in a chat using the power of AI LLM.
The telegram bots are not allowed to read the chat history, so we need to store the messages in the database. Right now the bot is using the Firestore database.
For summarizing the messages, the bot is using the OpenAI API. 

💰 The OpenAI API **is not free**, so you need to have an account and generate the API key. 💰 

## Presetup
1. Rename .example.env to .env.
2. Setup the Firestore database. [Instruction](https://medium.com/@androidcrypto/setup-of-a-cloud-firestore-database-tutorial-step-by-step-1ccc9ec52005) 
3. Go to [IAM & admin > Service](https://console.cloud.google.com/iam-admin/serviceaccounts) accounts in the Google Cloud console. Generate a new private key and save the JSON file. Then use the file to initialize the SDK. Save this file as `serviceAccountKey.json` in the root directory.
4. Create a new bot using the [BotFather](https://core.telegram.org/bots#6-botfather) and get the token. Save the token in the `.env` file.
5. In `.env` file set the `TELEGRAM_BOT_NAME` variable to the bot name **without** @.
```
TELEGRAM_BOT_NAME=your_bot_name
```   
6. Change the bot privacy settings to disable the "Group Privacy" option.
    * Go to BotFather in Telegram send `/setprivacy`.
    * Select the username of the bot.
    * Select Disable.
7. Generate the [OpenAI API](https://platform.openai.com/api-keys) key and save it in the `.env` file.

## Run on server
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
If you want to run it with pm2 run the following command after activating venv:
```bash
pm2 start main.py --name summarizer_bot
```
## Usage
### Required steps
1. Add the bot to the chat.
2. Send the `/start` command to the bot.
3. Send the `/chatid` command to the bot to get the chat id.
4. **Create in the Firestore database a collection with the name of the chat id.**

### Commands
- `/start` - Start the bot.
- `/chatid` - Get the chat ID.
- `/summarize n` - Summarize the last n messages in the chat. If n is not provided, the bot will summarize the last 50 messages.
- `/ironic n` - Summarize the last n messages in the chat in an ironic manner. If n is not provided, the bot will summarize the last 50 messages.
  