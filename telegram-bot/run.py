import os
import logging
import requests
from dotenv import load_dotenv

from telegram import CallbackQuery, ForceReply, InlineKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from app.initialize_logging import logger
from app.lib.bot_commands.escrow import escrow_command
from app.lib.bot_commands.help import help_command
from app.lib.bot_commands.start import default_response, start

load_dotenv()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles callback queries
    """
    callback_query = update.callback_query
    data = callback_query.data

    if data.startswith("seller_cancel_"):
        session_id = data.split("_")[1]

        URL = os.environ["BACKEND_API"]
        response = requests.post(
                f"{URL}/cancel_payment",
                json={
                    "session_id": session_id
                }).json()


        await callback_query.message.edit_text("Escrow session cancelled.")
    elif data.startswith("seller_confirm_"):
        session_id = data.split("_")[-1]
        # Confirm the payment
        # You can implement the logic to confirm the payment here
        URL = os.environ["BACKEND_API"]
        response = requests.post(
                f"{URL}/confirm_payment",
                json={
                    "session_id": session_id
                }).json()

        if 'error' in response:
            message = "Payment not found. Please try again."

            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data=f"seller_cancel_{session_id}"),
                    InlineKeyboardButton("Confirm Payment", callback_data=f"seller_confirm_{session_id}"),
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(
                message,
                reply_markup=reply_markup
            )
            return

        tx_hash = response['result']
        user_id = response['buyer_user_id']
        await callback_query.message.edit_text(f"Payment confirmed. Escrow session initialized. {tx_hash}")

        keyboard = [
            [
                InlineKeyboardButton("Cancel Escrow", callback_data=f"buyer_cancel_escrow_{session_id}"),
                InlineKeyboardButton("Confirm Payment", callback_data=f"buyer_confirm_payment_{session_id}"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text="Payment confirmed. Escrow session initialized, Please pay the seller and hit confirm.", reply_markup=reply_markup)


def main() -> None:
    """Start the bot."""
    logger.info("Starting Bot.")
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("escrow", escrow_command))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, default_response)
    )
    logger.info("Bot is ready.")

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
