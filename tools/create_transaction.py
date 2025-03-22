import argparse
import os

import requests
from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

# Load environment variables
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL", "http://localhost:8000")

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Send Ethereum transaction or generate a private key."
)
parser.add_argument("amount", type=float, nargs="?", help="Amount of ETH to send")
parser.add_argument("recipient", type=str, nargs="?", help="Recipient Ethereum address")
parser.add_argument(
    "--generate-key", action="store_true", help="Generate a new private key"
)
parser.add_argument(
    "--mode",
    choices=["rpc", "alchemy"],
    default="rpc",
    help="Choose between RPC or Alchemy-like interface",
)
args = parser.parse_args()

# Generate a private key if requested
if args.generate_key:
    new_account = Account.create()
    print("Generated Private Key:", new_account.key.hex())
    print("Address:", new_account.address)
    exit()

# Ensure amount and recipient are provided for a transaction
if args.amount is None or args.recipient is None:
    parser.error("Amount and recipient address are required unless generating a key.")

# Initialize Web3 instance
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Define the transaction
tx = {
    "to": args.recipient,
    "value": w3.to_wei(args.amount, "ether"),
    "gas": 21000,
    "maxPriorityFeePerGas": w3.to_wei(5, "gwei"),
    "maxFeePerGas": w3.to_wei(30, "gwei"),
    "nonce": w3.eth.get_transaction_count(w3.eth.account.from_key(PRIVATE_KEY).address),
    "chainId": 6443,
    "type": "0x2",  # EIP-1559 transaction
}

# Sign the transaction
signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)


def send_transaction_rpc():
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print("Transaction sent. Transaction Hash:", tx_hash.hex())

        # Wait for the transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Transaction mined!")
        print("Transaction Receipt:")
        print(tx_receipt)
    except Exception as e:
        print("Error sending transaction:", str(e))


def send_transaction_alchemy():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_sendRawTransaction",
        "params": [f"0x{signed_tx.raw_transaction.hex()}"],
        "id": 1,
    }
    try:
        alchemy_url = RPC_URL
        alchemy_url = "http://localhost:8000"
        response = requests.post(f"{alchemy_url}/eth_sendRawTransaction", json=payload)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise Exception(result["error"]["message"])

        tx_hash = result["result"]
        print("Transaction sent. Transaction Hash:", tx_hash)
        print(
            "Transaction submitted successfully. Check your wallet or a block explorer for confirmation."
        )
    except Exception as e:
        print("Error sending transaction:", str(e))


# Send the transaction based on the chosen mode
if args.mode == "rpc":
    send_transaction_rpc()
else:
    send_transaction_alchemy()
