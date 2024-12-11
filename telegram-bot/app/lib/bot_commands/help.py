from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from app.initialize_logging import logger


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_message = """
    Welcome to CryptoIndia Escrow Telegram Bot!

    This bot provides a USDT escrow service. Here are the available commands:

    /help - Displays this help message.
    /escrow <Network codename> <Public Address> - Initiates the escrow service.

    Supported Networks:
        Arbitrum (code_name: arb)
        Polygon (code_name: polygon),
        BNB Smart Chain (code_name: bsc)

    Eg:
        /escrow user_name arb 500 0xb0b3682211533cb7c1a3bcb0e0dd4349ff000d75


    Please note that this is a pre-alpha bot and you should not use it for actual transactions!
    """
    user = update.effective_user.username
    logger.info(f"User performed /help: {user}")
    await update.message.reply_text(help_message)
