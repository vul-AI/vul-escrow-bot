from app.libs.database import database
from app.libs.crypto.payments import create_wallet, get_wallet_address
import uuid


def escrow_initiation(
    seller_user_name, buyer_user_name, amount, network, buyer_wallet_address
):
    """
    The initiation involves the creation of an address, session_id and db requirements
    """

    session_id = str(uuid.uuid4())
    user_private_wallet_address = create_wallet()

    database.new_escrow_session(
        session_id = session_id,
        seller_user_name=seller_user_name,
        buyer_user_name=buyer_user_name,
        amount=amount,
        network=network,
        buyer_wallet_address=buyer_wallet_address,
        user_public_wallet_address=get_wallet_address(
            private_key=user_private_wallet_address
        ),
        user_private_wallet_address=user_private_wallet_address,
    )

    return session_id
