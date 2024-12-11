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

arb_w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))
ARB_USDT_ERC_20_TOKEN_ADDRESS = "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"
