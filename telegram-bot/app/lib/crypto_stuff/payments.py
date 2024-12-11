import datetime
import os
import web3
from web3 import Web3, Account

from pprint import pprint

import os
import sys
from decimal import Decimal

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider, Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from eth_defi.abi import get_deployed_contract
from eth_defi.token import Contract, fetch_erc20_details
from eth_defi.confirmation import wait_transactions_to_complete


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


def make_transaction(w3, contract_address, private_key, to_address, value):

    erc_20_contract = get_deployed_contract(
        arb_w3, "ERC20MockDecimals.json", contract_address
    )
    sender_pub = get_wallet_address(private_key)
    token_details = fetch_erc20_details(w3, contract_address)

    if not w3.is_checksum_address(to_address):
        return {"error": f"{to_address} is an invalid address."}

    if get_token_balance(sender_pub, erc_20_contract) < value:
        return {
            "error": f"Not enough {token_details.symbol} present? Did you send the complete amount?"
        }
    print(
        f"You have {get_token_balance(sender_pub, erc_20_contract)} {token_details.symbol}"
    )

    if w3.is_address(to_address):
        pass
    else:
        print("Address not valid address")
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
    approve_txn["gas"] = w3.eth.estimate_gas(approve_txn)

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

    transfer_txn["gas"] = w3.eth.estimate_gas(approve_txn)
    signed_txn = w3.eth.account.sign_transaction(transfer_txn, private_key)

    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    print(f"Broadcasted transaction {tx_hash.hex()}, now waiting 5 minutes for mining")
    wait_transactions_to_complete(
        w3, [tx_hash], max_timeout=datetime.timedelta(minutes=7)
    )


def find_transaction(w3, private_key, value):
    """
    Finds the latest transaction using the public key of a wallet for a particular amount.

    Args:
        w3 (Web3 object): A Web3 object connected to the Ethereum network.
        private_key (str): The private key of the wallet.
        value (int): The amount to search for in the transactions.

    Returns:
        str: The transaction hash of the latest transaction, or None if no transaction is found.
    """
    public_address = get_wallet_address(private_key)
    tx_count = w3.eth.get_transaction_count(public_address)
    for i in range(tx_count, 0, -1):
        tx = w3.eth.get_transaction_by_block_number_and_index(i, 0)
        if (
            tx and tx.value == value and tx.blockNumber > w3.eth.block_number - 5760
        ):  # 5760 is the number of blocks in 24 hours
            return tx.hash.hex()
    return None
