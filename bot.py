import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, JobQueue

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Credentials (Yahan Tumhare API Details Hain)
API_ID = 24389326  
API_HASH = "e516c423e3edd76854e1c0741863f6f0"
BOT_TOKEN = "7606038780:AAGiQs757sNQDp1rrJdPvOHqPyjnFn-S83o"
GROUP_ID = -1002378088102  # Group ID jisme bot admin hai

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

async def remove_user_callback(context: CallbackContext):
    """Callback function to remove user from group."""
    job = context.job
    user_id = job.data

    try:
        await context.bot.ban_chat_member(GROUP_ID, user_id)
        await context.bot.send_message(
            GROUP_ID, 
            f"✅ User {user_id} removed from the group."
        )
        logger.info(f"User {user_id} removed successfully.")

    except Exception as e:
        await context.bot.send_message(GROUP_ID, f"❌ Error removing user {user_id}: {str(e)}")
        logger.error(f"Error removing user {user_id}: {str(e)}")

async def remove_user(update: Update, context: CallbackContext):
    """Handle /remove_user command to schedule user removal from group."""
    try:
        args = context.args
        if not args or len(args) < 2:
            await update.message.reply_text("Usage: /remove_user user_id time (e.g., /remove_user 123456789 10s,5m,1h)")
            return

        user_id = args[0]
        if not user_id.isdigit():
            await update.message.reply_text("Error: Invalid user ID format.")
            return
        user_id = int(user_id)

        time_str = args[1]
        time_in_seconds = time_to_seconds(time_str)

        if time_in_seconds <= 0:
            await update.message.reply_text("Invalid time format! Use s (seconds), m (minutes), h (hours), d (days).")
            return

        await update.message.reply_text(f"✅ User {user_id} will be removed after {time_str}.")
        
        # Schedule Job
        context.job_queue.run_once(remove_user_callback, time_in_seconds, data=user_id, chat_id=GROUP_ID)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Error in /remove_user: {str(e)}")

async def start(update: Update, context: CallbackContext):
    """Start command response."""
    await update.message.reply_text("Hello! Use /remove_user user_id time to remove a user after a set time.")

async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remove_user", remove_user))

    logger.info("🚀 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
