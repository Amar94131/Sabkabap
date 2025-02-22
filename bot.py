import os
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telethon import TelegramClient
from telethon.errors import PeerIdInvalidError, UserNotParticipantError

# Load environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel username or ID

# Initialize Telethon client in bot mode
client = TelegramClient("bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Initialize Telegram Bot API
app = Application.builder().token(BOT_TOKEN).build()


def time_to_seconds(time_str):
    """Convert time format (10s,5m,1h,1d) into seconds."""
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    total_seconds = 0
    matches = re.findall(r"(\d+)([smhd])", time_str)

    for value, unit in matches:
        total_seconds += int(value) * time_units[unit]

    return total_seconds


async def remove_user(update: Update, context: CallbackContext):
    """Handle /remove_user command to schedule user removal."""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /remove_user user_id time (e.g., /remove_user 123456789 10s,5m,1h)")
            return

        user_id = int(args[0])
        time_str = args[1]
        time_in_seconds = time_to_seconds(time_str)

        if time_in_seconds <= 0:
            await update.message.reply_text("Invalid time format! Use s (seconds), m (minutes), h (hours), d (days).")
            return

        if not CHANNEL_ID:
            await update.message.reply_text("Error: CHANNEL_ID is not set. Please check bot settings.")
            return

        async with client:
            try:
                user = await client.get_entity(user_id)  # Validate user
            except PeerIdInvalidError:
                await update.message.reply_text("Error: Invalid user ID.")
                return

            # Check if user is already in the channel
            try:
                participants = await client.get_participants(CHANNEL_ID)
                if not participants:
                    await update.message.reply_text("Error: Unable to fetch participants. Check bot's admin rights.")
                    return

                user_ids = [p.id for p in participants]
                if user_id not in user_ids:
                    await update.message.reply_text("User is not in the channel.")
                    return
            except Exception as e:
                await update.message.reply_text(f"Error checking user in channel: {str(e)}")
                return

        await update.message.reply_text(f"✅ User {user_id} will be removed after {time_str}.")

        # Schedule the user removal
        await asyncio.sleep(time_in_seconds)
        try:
            await client.kick_participant(CHANNEL_ID, user_id)
            await update.message.reply_text(f"✅ User {user_id} removed from {CHANNEL_ID}.")
        except UserNotParticipantError:
            await update.message.reply_text(f"⚠ User {user_id} is not in the channel.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error removing user {user_id}: {str(e)}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def start(update: Update, context: CallbackContext):
    """Start command response."""
    await update.message.reply_text("Hello! Use /remove_user user_id time to remove a user after a set time.")


def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remove_user", remove_user))

    print("🚀 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
