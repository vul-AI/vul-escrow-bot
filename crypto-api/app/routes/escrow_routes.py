from flask import Blueprint, jsonify, request
from dotenv import load_dotenv

load_dotenv()

from app.initialize_logging import logger

from app.libs.crypto.payments import (
    find_sender_wallet,
    find_transaction,
    get_network_details,
    make_transaction_usd_tokens,
)
from app.libs.database.database import (
    get_escrow_details,
    get_public_wallet_address,
    get_user,
)
from app.libs.interface.escrow import escrow_initiation

escrow_blueprint = Blueprint("escrow_blueprint", __name__)


@escrow_blueprint.route("/initialize_escrow", methods=["GET", "POST"])
def route_initialize_escrow():
    """
    Initalizes the escrow service.

    Required:
        seller_user_name: user_name of the seller
        buyer_user_name: user_name of the buyer
        amount: amount involved in the trade
        network: which network? (Arb, Polygon, BSC)
        buyer_wallet_address: address of the buyer
    """
    if request.method == "GET":
        return (
            jsonify({"error": "GET method is not allowed for this route. Do POST."}),
            405,
        )

    data = request.get_json()
    seller_user_name = data.get("seller_user_name")
    buyer_user_name = data.get("buyer_user_name")
    amount = data.get("amount")
    network = data.get("network")
    buyer_wallet_address = data.get("buyer_wallet_address")

    allowed_networks = ["arb", "poly", "bsc", "sep"]
    if network not in allowed_networks:
        logger.error("Invalid network. Allowed networks are: %s", allowed_networks)
        return (
            jsonify(
                {
                    "error": "Invalid network. Implemented networks include Arb, Poly or BSC."
                }
            ),
            400,
        )

    session_id = escrow_initiation(
        seller_user_name=seller_user_name,
        buyer_user_name=buyer_user_name,
        amount=amount,
        network=network,
        buyer_wallet_address=buyer_wallet_address,
    )

    return jsonify({"session_id": session_id}), 200


@escrow_blueprint.route("/get_public_wallet_address", methods=["POST"])
def route_get_public_wallet_address():
    """
    Gets the public address involved in the escrow trade for the session_id.
    """
    if request.method == "GET":
        return (
            jsonify({"error": "GET method is not allowed for this route. Do POST."}),
            405,
        )

    req = request.get_json()
    session_id = req.get("session_id")

    wallet_address = get_public_wallet_address(session_id=session_id)

    if wallet_address == None:
        return jsonify({"error": "session_id does not exist."}), 400

    return jsonify({"public_wallet_address": wallet_address}), 200


@escrow_blueprint.route("/confirm_payment", methods=["POST"])
def route_confirm_payment():
    """
    Checks if the user actually paid to the public wallet associated to the session_id or not
    """

    req = request.get_json()
    session_id = req.get("session_id")
    logger.info(f"confirming escrow for {session_id}")

    escrow_details = get_escrow_details(session_id=session_id)
    if escrow_details is None:
        return (
            jsonify(
                {
                    "error": "Session was not added to db. Please contact developer or admin."
                }
            ),
            400,
        )

    public_wallet_address = escrow_details["user_public_wallet_address"]
    network = escrow_details["network"]
    amount = escrow_details["amount"]
    total_amount = amount + amount * 5 / 100

    tx_hash = find_transaction(public_wallet_address, network, total_amount)

    logger.info(f"Found transaction hash at: {tx_hash}")

    if tx_hash is None:
        return jsonify({"error": "Payment not made. Please make payment."}), 300

    return (
        jsonify(
            {
                "result": f'Payment hash: {tx_hash["hash"]}',
                "buyer_user_id": get_user(session_id),
            }
        ),
        200,
    )


@escrow_blueprint.route("/cancel_escrow", methods=["POST"])
def route_cancel_escrow():
    """
    Cancels the escrow
    """

    req = request.get_json()
    session_id = req.get("session_id")

    escrow_details = get_escrow_details(session_id=session_id)
    if escrow_details is None:
        return (
            jsonify(
                {
                    "error": "Session was not added to db. Please contact developer or admin."
                }
            ),
            400,
        )

    user_public_wallet_address = escrow_details["user_public_wallet_address"]
    user_private_wallet_address = escrow_details["user_private_wallet_address"]
    network = escrow_details["network"]
    amount = escrow_details["amount"]
    total_amount = amount + amount * 5 / 100

    w3, _, _, _ = get_network_details(network=network)

    tx_hash = find_transaction(user_public_wallet_address, network, total_amount)

    if tx_hash is None:
        return jsonify({"result": "Payment not made. Canceling."}), 200

    sender_wallet_address = find_sender_wallet(w3, tx_hash)

    # TODO: send txn hash back, seems like you removed it past varoo
    send_back_tx_hash = make_transaction_usd_tokens(
        network, user_private_wallet_address, sender_wallet_address, amount
    )

    return jsonify({"result": f"Payment hash: {tx_hash}"})


# TODO: Write code for completition of escrow service
@escrow_blueprint.route("/complete_escrow", methods=["POST"])
def route_complete_escrow():
    req = request.get_json()
    session_id = req.get("session_id")

    escrow_details = get_escrow_details(session_id=session_id)
    if escrow_details is None:
        return jsonify({"error": "No session id found"}), 400

    buyer_wallet_address = escrow_details["buyer_wallet_address"]
    network = escrow_details["network"]
    user_private_wallet_address = escrow_details["user_private_wallet_address"]
    amount = escrow_details["amount"]

    # TODO: send txn hash back, seems like you removed it past varoo
    make_transaction_usd_tokens(
        network, user_private_wallet_address, buyer_wallet_address, amount
    )

    return jsonify({"not_implemented": True, "result": "Completed."}), 200
