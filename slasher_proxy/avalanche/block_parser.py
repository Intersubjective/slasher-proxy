import json

import requests
from pony.orm import commit, db_session

from slasher_proxy.common.model import Block, BlockTransaction, Transaction


def get_cchain_block_by_number(number):
    """
    Retrieve a C-Chain block by its number.
    The block number is passed as an integer which we convert to hex.
    """
    url = "https://api.avax.network/ext/bc/C/rpc"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBlockByNumber",
        "params": [hex(number), True],  # 'True' to include full transaction objects
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def get_platform_block_by_height(height):
    url = "https://api.avax.network/ext/bc/P"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "platform.getBlockByHeight",
        "params": {"height": height, "encoding": "json"},
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def parse_and_save_block(json_result):
    """
    Parse the JSON result from a C-Chain RPC call and save/update a Block,
    create Transaction records for each transaction and link them via BlockTransaction.
    """
    # For C-Chain, the block data is in result directly.
    block = json_result.get("result")
    if not block:
        return None

    with db_session:
        # Parse block-level fields.
        height = int(block.get("number"), 16) if block.get("number") else 0
        timestamp = int(block.get("timestamp"), 16) if block.get("timestamp") else 0

        # Convert the block hash from hex string to bytes.
        block_hash_str = block.get("hash", "")
        block_hash = (
            bytes.fromhex(block_hash_str[2:])
            if block_hash_str.startswith("0x")
            else block_hash_str.encode()
        )

        # For C-Chain, use the 'miner' field as the node identifier.
        node_id = block.get("miner", "unknown")

        # Create or update the Block record.
        db_block = Block.get(number=height)

        if not db_block:
            db_block = Block(
                number=height, hash=block_hash, node_id=node_id,
            )
        else:
            db_block.hash = block_hash
            db_block.node_id = node_id

        # Process transactions.
        txs = block.get("transactions", [])
        for order, tx in enumerate(txs, start=1):
            tx_hash_str = tx.get("hash")
            if not tx_hash_str:
                continue
            tx_hash = (
                bytes.fromhex(tx_hash_str[2:])
                if tx_hash_str.startswith("0x")
                else tx_hash_str.encode()
            )
            # Serialize the transaction as a canonical JSON string.
            raw_tx = json.dumps(tx, sort_keys=True)
            # Create or get the Transaction record.
            tx_obj = Transaction.get(hash=tx_hash)
            if not tx_obj:
                from_addr = tx.get("from", "unknown")
                nonce_str = tx.get("nonce", "0x0")
                nonce = int(nonce_str, 16) if isinstance(nonce_str, str) else 0
                tx_obj = Transaction(
                    hash=tx_hash,
                    from_address=from_addr,
                    nonce=nonce,
                )
            # Create a linking record if it doesn't exist.
            if not BlockTransaction.get(block=db_block, transaction=tx_obj):
                BlockTransaction(block=db_block, transaction=tx_obj, order=order)
        commit()

    return {
        "height": height,
        "timestamp": timestamp,
        "node_id": node_id,
        "hash": block_hash_str,
        "transaction_count": len(txs),
    }

