import os
import time
from dotenv import load_dotenv
import requests
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from app.initialize_logging import logger
# from app.lib.crypto_stuff import arb_network
# from app.lib.crypto_stuff import payments
# from app.lib.database import mongo_db

load_dotenv()

FEE_PERCENTAGE = 5


async def escrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Command will be /escrow <user_name> <Network> <Amount> <Buyer Public Address>.
    Extract the User Name and Network, Buyer Address from the command
    """
    args = context.args
    if args is None or len(args) != 4:
        # you can send an error message to the user if the command is not used correctly
        await update.effective_message.reply_text(
            "Usage: /escrow <Reciever User Name> <Network Name> <Amount> <Buyer Public Address>"
        )
        return

    sender_user_name = update.effective_user.username
    reciever_user_name = args[0]
    network = args[1].lower()
    amount = float(args[2])
    buyer_address = args[3]
    URL = os.environ['BACKEND_API']

    data = {
        'seller_user_name': sender_user_name,
        'buyer_user_name': reciever_user_name,
        'amount': amount,
        'network': network,
        'buyer_wallet_address': buyer_address
    }

    response = requests.post(URL + '/initialize_escrow', json=data).json()

    if 'error' in response:
        await update.effective_message.reply_text(
                f"There was an error: Please check error\n{response['error']}"
                )
        return

    logger.info(f"Response for initalization of escrow: {response}")

    session_id = response['session_id']

    response = requests.post(
            URL + '/get_public_wallet_address',
            json={'session_id': session_id}
        ).json()


    public_wallet = response['public_wallet_address']

    fee_amount = amount * FEE_PERCENTAGE / 100
    total_payable_amount = amount + fee_amount

    message = f"""
        Please pay {total_payable_amount} USDT to
        ```{public_wallet}```
        to initiate the escrow between you and @{reciever_user_name}.
        This amount includes a fee of {fee_amount} USDT ({FEE_PERCENTAGE}%) in addition to the {amount} USDT you want to send.
        """.split()

    message = " ".join(message)

    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data=f"seller_cancel_{session_id}"),
            InlineKeyboardButton("Confirm Payment", callback_data=f"seller_confirm_{session_id}"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


