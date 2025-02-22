import time
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID

# Logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize Telegram Client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Dictionary to store scheduled removals
scheduled_removals = {}

# Function to convert time units to seconds
def time_to_seconds(time_str):
    total_seconds = 0
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "mo": 2592000, "y": 31536000}

    time_parts = time_str.split(",")  # Example: "10s,5m,2h"
    for part in time_parts:
        unit = part[-1]  # Last character is unit (s, m, h, d, mo, y)
        if unit == "o":  # For 'mo' (month), check last two characters
            unit = "mo"
            value = int(part[:-2])
        elif unit == "y":  # For 'y' (year)
            value = int(part[:-1])
        else:
            value = int(part[:-1])

        if unit in time_units:
            total_seconds += value * time_units[unit]

    return total_seconds

# Command to add user with a specified time
def add_user(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 2:
            update.message.reply_text("Usage: /add_user user_id time (e.g., /add_user 123456789 10s,5m,1h)")
            return

        user_id = int(args[0])
        time_in_seconds = time_to_seconds(args[1])

        if time_in_seconds <= 0:
            update.message.reply_text("Invalid time format! Use s (seconds), m (minutes), h (hours), d (days), mo (months), y (years).")
            return

        # Promote user to the channel
        client.loop.run_until_complete(client.edit_admin(CHANNEL_ID, user_id, is_admin=True))
        update.message.reply_text(f"User {user_id} added for {args[1]}.")

        # Schedule removal
        scheduled_removals[user_id] = client.loop.call_later(time_in_seconds, remove_user, user_id)

    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

# Function to remove user after the set time
def remove_user(user_id):
    try:
        client.loop.run_until_complete(client.kick_participant(CHANNEL_ID, user_id))
        logging.info(f"User {user_id} removed from {CHANNEL_ID}.")
    except Exception as e:
        logging.error(f"Failed to remove user {user_id}: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("add_user", add_user))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
