import datetime
import os
import web3
from web3 import Web3, Account
import requests

from pprint import pprint

import os
import sys
from decimal import Decimal
from app.initialize_logging import logger

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider, Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from eth_defi.abi import get_deployed_contract
from eth_defi.token import Contract, fetch_erc20_details
from eth_defi.confirmation import wait_transactions_to_complete


def get_network_details(network: str):
    """
    Gets the network details
    """
    network = network.lower()

    if network == "arb":
        w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))
        USDT_ERC_20_TOKEN_ADDRESS = "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"
        api_url = "https://api.arbscan.io/api"
        API_KEY = os.environ["ARBSCAN_API"]

    # TODO: Change these
    elif network == "poly":
        w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))
        USDT_ERC_20_TOKEN_ADDRESS = (
            "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"  # need to change
        )
        api_url = "https://api-sepolia.etherscan.io/api"
        API_KEY = os.environ["ETHERSCAN_API"]

    elif network == "bsc":
        w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))
        USDT_ERC_20_TOKEN_ADDRESS = (
            "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"  # need to change
        )
        api_url = "https://api.bscscan.io/api"
        API_KEY = os.environ["BSCSCAN_API"]

    else:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.drpc.org/rpc"))
        USDT_ERC_20_TOKEN_ADDRESS = "0x2Ba9582c7D0e0c80Bc36c574f6Fa5eC7170eA9Ae"
        api_url = "https://api-sepolia.etherscan.io/api"
        API_KEY = os.environ["ETHERSCAN_API"]

    return w3, USDT_ERC_20_TOKEN_ADDRESS, api_url, API_KEY


def create_wallet():
    """
    Creates a new Ethereum wallet and returns its address and private key.

    Returns:
        tuple: A tuple containing the wallet address and private key as hexadecimal strings.
    """
    # Create a new Ethereum account
    private_key = Account.create()
    return private_key.key


def get_token_balance(public_address, token_contract):
    balance = token_contract.functions.balanceOf(public_address).call()
    return balance


def get_wallet_address(private_key):
    account = Account.from_key(private_key)
    return account.address


def make_transaction_usd_tokens(network, private_key, to_address, value):
    """
    Makes a transaction from a wallet to a specified address.

    Args:
        network (str): Name of network on which you want transaction to occur
        private_key (str): The private key of the wallet.
        to_address (str): The address to send the tokens to.
        value (int): The amount of tokens to send.

    Returns:
        None
    """

    w3, contract_address, _, _ = get_network_details(network)

    erc_20_contract = get_deployed_contract(
        w3, "ERC20MockDecimals.json", contract_address
    )
    sender_pub = get_wallet_address(private_key)
    token_details = fetch_erc20_details(w3, contract_address)

    if not w3.is_checksum_address(to_address):
        return {"error": f"{to_address} is an invalid address."}

    if get_token_balance(sender_pub, erc_20_contract) < value:
        return {
            "error": f"Not enough {token_details.symbol} present? Did you send the complete amount?"
        }
    logger.info(
        f"You have {get_token_balance(sender_pub, erc_20_contract)} {token_details.symbol}"
    )

    if w3.is_address(to_address):
        pass
    else:
        logger.info("Address not valid address")
        return

    raw_amount = token_details.convert_to_raw(value)
    approve_txn = erc_20_contract.functions.approve(
        sender_pub, raw_amount
    ).build_transaction(
        {
            "from": sender_pub,
            "nonce": w3.eth.get_transaction_count(sender_pub),
            "gasPrice": w3.to_wei("5", "gwei"),
        }
    )
    approval_gas_amount = w3.eth.estimate_gas(approve_txn)
    approve_txn["gas"] = approval_gas_amount
    get_gas_amount(w3, sender_pub, approval_gas_amount)

    signed_txn = w3.eth.account.sign_transaction(approve_txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    wait_transactions_to_complete(
        w3, [tx_hash], max_timeout=datetime.timedelta(minutes=1)
    )

    transfer_txn = erc_20_contract.functions.transfer(
        to_address, value
    ).build_transaction(
        {
            "from": sender_pub,
            "nonce": w3.eth.get_transaction_count(sender_pub),
            "gasPrice": w3.to_wei("5", "gwei"),  # Adjust gas price as needed
        }
    )

    gas_amount = w3.eth.estimate_gas(approve_txn)
    transfer_txn["gas"] = gas_amount
    get_gas_amount(w3, sender_pub, gas_amount)

    signed_txn = w3.eth.account.sign_transaction(transfer_txn, private_key)

    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    logger.info(
        f"Broadcasted transaction {tx_hash.hex()}, now waiting 5 minutes for mining"
    )
    wait_transactions_to_complete(
        w3, [tx_hash], max_timeout=datetime.timedelta(minutes=7)
    )


def get_gas_amount(w3, recipient_address, gas_amount):
    """
    Gets the estimated gas amount required for making a transaction from wallet MAIN.
    """

    main_wallet_private_key = os.environ["MAIN_ACCOUNT_KEY"]
    # w3, _, _, _ = get_network_details(network=network)
    sender_account = w3.eth.account.privateKeyToAccount(main_wallet_private_key)

    # Build and sign the transaction
    tx = {
        "to": recipient_address,
        "value": w3.toWei(gas_amount),
        "gas": 21000,
        "gasPrice": w3.eth.gasPrice,
    }
    signed_tx = sender_account.sign_transaction(tx)

    # Send the transaction
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    logger.info("Transaction Hash:", tx_hash.hex())

    # Wait for the transaction to be mined
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    logger.info("Transaction Receipt:", tx_receipt)


def find_transaction(wallet_address, network, value):
    w3, token_contract_address, url, api_key = get_network_details(network)

    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": token_contract_address,
        "address": wallet_address,
        "value": value * (10**18),
        "page": 1,
        "offset": 100,
        "startblock": 0,
        "endblock": 27025780,
        "sort": "asc",
        "apikey": api_key,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["result"][0]
    else:
        return None


def find_sender_wallet(w3, tx_hash):
    tx = w3.eth.get_transaction(tx_hash)
    return tx["from"]
