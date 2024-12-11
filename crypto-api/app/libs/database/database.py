from pymongo import MongoClient
from app.initialize_logging import logger
import os

client = MongoClient(os.environ["MONGO_DB_URL"])
db = client["Vul-Escrow-Test"]


def new_escrow_session(
    session_id: str,
    seller_user_name: str,
    buyer_user_name: str,
    amount: float,
    network,
    buyer_wallet_address: str,
    user_public_wallet_address: str,
    user_private_wallet_address: str,
):

    escrow_sessions = db["escrow_sessions"]

    escrow_session = {
        "session_id": session_id,
        "seller_user_name": seller_user_name,
        "buyer_user_name": buyer_user_name,
        "amount": amount,
        "network": network,
        "buyer_wallet_address": buyer_wallet_address,
        "user_public_wallet_address": user_public_wallet_address,
        "user_private_wallet_address": user_private_wallet_address,
        "status": "pending",
    }

    result = escrow_sessions.insert_one(escrow_session)

    return result.inserted_id


def get_public_wallet_address(session_id: str) -> str | None:
    """
    Retrieves the public wallet address from the database for a given `session_id`.
    """
    escrow_sessions = db["escrow_sessions"]
    query = {"session_id": session_id}
    escrow_session = escrow_sessions.find_one(query)

    if escrow_session:
        return escrow_session["user_public_wallet_address"]
    else:
        logger.error("Escrow session not found for session_id: %s", session_id)
        return None


users = db["user_details"]


def get_escrow_details(session_id: str):
    escrow_sessions = db["escrow_sessions"]
    query = {"session_id": session_id}
    escrow_session = escrow_sessions.find_one(query)

    if escrow_session:
        return escrow_session
    else:
        logger.error("Escrow session not found for session_id: %s", session_id)
        return None


def insert_user(user_name: str, user_id: str):
    """
    Insert the user Id and user_name for events when bot needs to communicate between two users
    """
    user = {
        "user_name": user_name,
        "user_id": user_id,
    }
    result = users.update_one({"user_name": user_name}, {"$set": user}, upsert=True)
    return result


def get_user(session_id: str):
    escrow_details = get_escrow_details(session_id)
    buyer_user_name = escrow_details["buyer_user_name"]

    query = {"user_name": buyer_user_name}
    user = users.find_one(query)
    if user:
        return user["user_id"]
    else:
        logger.error("User not found for user_name: %s", buyer_user_name)
        return None
