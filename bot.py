import os
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telethon import TelegramClient, functions, types, errors

# Load environment variables
API_ID = int(os.getenv("API_ID", "24389326"))  
API_HASH = os.getenv("API_HASH", "e516c423e3edd76854e1c0741863f6f0")  
BOT_TOKEN = os.getenv("BOT_TOKEN", "7606038780:AAGiQs757sNQDp1rrJdPvOHqPyjnFn-S83o")  
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1002156040011")  

if CHANNEL_ID.startswith("-100"):
    CHANNEL_ID = int(CHANNEL_ID)

# Initialize Telethon Client WITH session (Fix)
client = TelegramClient("bot_session", API_ID, API_HASH)

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
            await client.connect()  # Ensure connection is established
            
            if not await client.is_user_authorized():
                await update.message.reply_text("Error: Bot is not authorized. Please check API credentials.")
                return

            try:
                user = await client.get_entity(user_id)  # Validate user
            except errors.PeerIdInvalidError:
                await update.message.reply_text("Error: Invalid user ID.")
                return

            # Check if user is in the channel
            try:
                participant = await client(functions.channels.GetParticipantRequest(CHANNEL_ID, user_id))
                if not participant:
                    await update.message.reply_text("User is not in the channel.")
                    return
            except errors.UserNotParticipantError:
                await update.message.reply_text("User is not in the channel.")
                return

        await update.message.reply_text(f"✅ User {user_id} will be removed after {time_str}.")

        # Schedule the user removal
        await asyncio.sleep(time_in_seconds)
        async with client:
            await client.connect()  
            try:
                await client(functions.channels.EditBannedRequest(
                    CHANNEL_ID,
                    user_id,
                    types.ChatBannedRights(until_date=None, view_messages=True)  # Bans user permanently
                ))
                await update.message.reply_text(f"✅ User {user_id} removed from {CHANNEL_ID}.")
            except errors.UserNotParticipantError:
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
