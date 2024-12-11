import os

from dotenv import load_dotenv
from app.initialize_logging import logger
import requests

from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

URL = os.environ["BACKEND_API"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    if user is None:
        logger.info("User does not exist")
        return

    user_data = {'user_id': user.id, 'user_name': user.username}
    response = requests.post(URL + '/add_user', json=user_data)
    if response.status_code != 200:
        logger.error("Failed to add user to backend API")

    logger.info(f"User started bot: {user}")
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def default_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text("Hey there, use /escrow to start services")
